from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import requests

from logger import setup_logger
from topic_filter import SENSITIVE_KEYWORDS

KST = "Asia/Seoul"
OUTPUT_DIR = Path("output") / "daily_issue"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class IssueSignal:
    text: str
    source: str
    signal_type: str
    weight: int
    url: str = ""


@dataclass(frozen=True)
class DailyIssue:
    title: str
    keywords: list[str]
    score: int
    reason: str
    news_sources: list[str]
    trend_sources: list[str]
    social_hint_sources: list[str]
    supporting_links: list[str]
    generated_at: str


class DailyIssueCollector:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def collect(self) -> DailyIssue | None:
        self.logger.info("daily issue 수집 시작")
        signals = []
        signals.extend(self._collect_news_signals())
        trend_signals = self._collect_google_trends_signals()
        signals.extend(trend_signals)
        signals.extend(self._collect_social_hint_signals(trend_signals))

        filtered = [signal for signal in signals if not _contains_sensitive_keyword(signal.text)]
        if not filtered:
            self.logger.warning("daily issue 후보가 없습니다.")
            return None

        issue = self._select_top_issue(filtered)
        if issue is None:
            self.logger.warning("daily issue 선정 실패")
            return None

        self.logger.info("daily issue 선정 | %s | score=%s", issue.title, issue.score)
        return issue

    def _collect_news_signals(self) -> list[IssueSignal]:
        feeds = [
            ("연합뉴스 최신뉴스", "https://www.yna.co.kr/rss/news.xml"),
            ("연합뉴스 정치 제외 주요뉴스", "https://www.yna.co.kr/rss/mostviewed.xml"),
        ]
        collected: list[IssueSignal] = []

        for label, url in feeds:
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                for item in root.findall(".//item")[:20]:
                    title = _clean_text(item.findtext("title", default=""))
                    link = item.findtext("link", default="").strip()
                    if title:
                        collected.append(
                            IssueSignal(
                                text=title,
                                source=label,
                                signal_type="news",
                                weight=6,
                                url=link,
                            )
                        )
            except Exception as error:  # noqa: BLE001
                self.logger.warning("뉴스 수집 실패 | %s | %s", label, error)

        return collected

    def _collect_google_trends_signals(self) -> list[IssueSignal]:
        endpoints = (
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
            "https://trends.google.com/trending/rss?geo=KR",
        )
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint, timeout=15)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                items = []
                for item in root.findall(".//item")[:20]:
                    title = _clean_text(item.findtext("title", default=""))
                    link = item.findtext("link", default="").strip()
                    if title:
                        items.append(
                            IssueSignal(
                                text=title,
                                source="Google Trends RSS",
                                signal_type="trend",
                                weight=4,
                                url=link,
                            )
                        )
                if items:
                    return items
            except Exception as error:  # noqa: BLE001
                self.logger.warning("트렌드 수집 실패 | %s | %s", endpoint, error)
        return []

    def _collect_social_hint_signals(self, trend_signals: list[IssueSignal]) -> list[IssueSignal]:
        collected: list[IssueSignal] = []
        seeds = [signal.text for signal in trend_signals[:10]]
        for seed in seeds:
            try:
                response = self.session.get(
                    "https://suggestqueries.google.com/complete/search",
                    params={"client": "firefox", "hl": "ko", "gl": "kr", "q": seed},
                    timeout=15,
                )
                response.raise_for_status()
                payload = json.loads(response.text)
                suggestions = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
                for suggestion in suggestions[:5]:
                    text = _clean_text(str(suggestion))
                    if text:
                        collected.append(
                            IssueSignal(
                                text=text,
                                source=f"Google Suggest ({seed})",
                                signal_type="social_hint",
                                weight=2,
                            )
                        )
            except Exception as error:  # noqa: BLE001
                self.logger.warning("소셜 힌트 수집 실패 | %s | %s", seed, error)
        return collected

    def _select_top_issue(self, signals: list[IssueSignal]) -> DailyIssue | None:
        news_signals = [signal for signal in signals if signal.signal_type == "news"]
        if not news_signals:
            return None

        scored: list[tuple[int, IssueSignal, list[str], list[IssueSignal]]] = []
        for signal in news_signals:
            keywords = _extract_keywords(signal.text)
            if not keywords:
                continue

            matched: list[IssueSignal] = []
            score = signal.weight
            for candidate in signals:
                if candidate is signal:
                    continue
                if _signals_match(signal.text, candidate.text, keywords):
                    matched.append(candidate)
                    score += candidate.weight

            scored.append((score, signal, keywords, matched))

        if not scored:
            return None

        scored.sort(key=lambda item: (-item[0], item[1].text))
        top_score, top_signal, keywords, matched = scored[0]

        news_sources = sorted({item.source for item in matched if item.signal_type == "news"} | {top_signal.source})
        trend_sources = sorted({item.source for item in matched if item.signal_type == "trend"})
        social_sources = sorted({item.source for item in matched if item.signal_type == "social_hint"})
        links = [top_signal.url] + [item.url for item in matched if item.url]

        reason_parts = [
            f"뉴스 {1 + len([item for item in matched if item.signal_type == 'news'])}건이 같은 이슈를 반복 언급",
        ]
        if trend_sources:
            reason_parts.append("Google Trends 신호와 겹침")
        if social_sources:
            reason_parts.append("검색 제안 기반 소셜 힌트가 따라붙음")

        return DailyIssue(
            title=top_signal.text,
            keywords=keywords[:5],
            score=top_score,
            reason=" / ".join(reason_parts),
            news_sources=news_sources,
            trend_sources=trend_sources,
            social_hint_sources=social_sources,
            supporting_links=_unique_nonempty(links)[:8],
            generated_at=datetime.now().isoformat(),
        )


def save_issue(issue: DailyIssue) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "today_issue.json"
    output_path.write_text(
        json.dumps(asdict(issue), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def _extract_keywords(text: str) -> list[str]:
    cleaned = re.sub(r"\[[^\]]+\]", " ", text)
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)
    tokens = re.findall(r"[0-9A-Za-z가-힣]{2,}", cleaned)
    stopwords = {
        "오늘",
        "한국",
        "종합",
        "속보",
        "단독",
        "이슈",
        "정부",
        "관련",
        "기자",
        "발표",
        "논란",
        "최신",
        "뉴스",
    }
    keywords = []
    for token in tokens:
        lowered = token.lower()
        if lowered in stopwords:
            continue
        if token not in keywords:
            keywords.append(token)
    return keywords


def _signals_match(base_text: str, candidate_text: str, keywords: list[str]) -> bool:
    base_norm = _normalize_text(base_text)
    cand_norm = _normalize_text(candidate_text)
    overlap = 0
    for keyword in keywords:
        keyword_norm = _normalize_text(keyword)
        if keyword_norm and keyword_norm in base_norm and keyword_norm in cand_norm:
            overlap += 1
    return overlap >= 1


def _normalize_text(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", text.lower())


def _contains_sensitive_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in SENSITIVE_KEYWORDS)


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _unique_nonempty(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def main() -> None:
    logger = setup_logger(Path("logs") / "daily_issue.log")
    collector = DailyIssueCollector(logger=logger)
    issue = collector.collect()
    if issue is None:
        raise SystemExit(1)
    output_path = save_issue(issue)
    print(f"daily issue saved: {output_path}")
    print(json.dumps(asdict(issue), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
