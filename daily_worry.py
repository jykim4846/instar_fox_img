from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import requests

from logger import setup_logger
from topic_filter import SENSITIVE_KEYWORDS

OUTPUT_DIR = Path("output") / "daily_worry"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

WORRY_HINT_PATTERNS = (
    "고민",
    "어떡",
    "어쩌",
    "해야 하나",
    "해도 되나",
    "해도 될까",
    "말아야 하나",
    "계속 만나",
    "버텨야 하나",
    "손절",
    "읽씹",
    "답장 느린",
    "퇴사",
    "이직",
    "안 맞",
    "왜 이럴",
    "이상한가",
    "맞나",
)

NORMALIZATION_RULES: list[tuple[tuple[str, ...], str]] = [
    (("답장", "읽씹", "카톡", "연락 텀", "연락"), "답장 느린 사람 계속 만나도 되나"),
    (("퇴사", "회사 안 맞", "이직", "버텨야 하나"), "회사 안 맞는데 버텨야 하나"),
    (("손절", "거리 둬", "불편한 친구", "친구"), "불편한 친구 계속 봐야 하나"),
    (("무지출", "절약", "소비", "가계부", "쇼핑"), "아끼려다 더 쓰는 습관 끊어야 하나"),
    (("루틴", "갓생", "자기관리", "운동", "습관"), "이번에도 루틴 작심삼일이면 어떻게 바꿔야 하나"),
]


@dataclass(frozen=True)
class WorrySignal:
    text: str
    source: str
    signal_type: str
    weight: int
    url: str = ""


@dataclass(frozen=True)
class RankedWorry:
    worry: str
    normalized_worry: str
    story: list[str]
    score: int
    reason: str
    matched_signals: list[str]
    supporting_links: list[str]


class DailyWorryCollector:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def collect(self) -> list[RankedWorry]:
        self.logger.info("daily worry 수집 시작")
        signals = self._collect_google_trends() + self._collect_google_suggest()
        filtered = [signal for signal in signals if self._is_candidate_worry(signal.text)]
        normalized = self._group_worries(filtered)
        ranked = self._rank_groups(normalized)
        self.logger.info("daily worry 수집 종료 | %s건", len(ranked))
        return ranked[:3]

    def _collect_google_trends(self) -> list[WorrySignal]:
        endpoints = (
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
            "https://trends.google.com/trending/rss?geo=KR",
        )
        collected: list[WorrySignal] = []
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint, timeout=15)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                for item in root.findall(".//item")[:20]:
                    title = _clean_text(item.findtext("title", default=""))
                    link = item.findtext("link", default="").strip()
                    if title:
                        collected.append(
                            WorrySignal(
                                text=title,
                                source="Google Trends RSS",
                                signal_type="trend",
                                weight=4,
                                url=link,
                            )
                        )
                if collected:
                    break
            except Exception as error:  # noqa: BLE001
                self.logger.warning("트렌드 수집 실패 | %s | %s", endpoint, error)
        return collected

    def _collect_google_suggest(self) -> list[WorrySignal]:
        seeds = [
            "퇴사 고민",
            "연애 고민",
            "답장 느린 사람",
            "손절해야 하나",
            "회사 안 맞음",
            "친구 거리두기",
            "돈 모으기 고민",
            "루틴 고민",
            "읽씹 고민",
            "이직 고민",
        ]
        collected: list[WorrySignal] = []
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
                for suggestion in suggestions[:8]:
                    text = _clean_text(str(suggestion))
                    if text:
                        collected.append(
                            WorrySignal(
                                text=text,
                                source=f"Google Suggest ({seed})",
                                signal_type="suggest",
                                weight=3,
                            )
                        )
            except Exception as error:  # noqa: BLE001
                self.logger.warning("suggest 수집 실패 | %s | %s", seed, error)
        return collected

    def _is_candidate_worry(self, text: str) -> bool:
        lowered = text.lower()
        if _contains_sensitive_keyword(lowered):
            return False
        if len(_normalize_text(text)) < 4:
            return False
        if any(pattern in lowered for pattern in WORRY_HINT_PATTERNS):
            return True
        return any(token in lowered for token in ("연애", "회사", "친구", "소비", "루틴", "답장"))

    def _group_worries(self, signals: list[WorrySignal]) -> dict[str, list[WorrySignal]]:
        grouped: dict[str, list[WorrySignal]] = {}
        for signal in signals:
            normalized = _normalize_worry(signal.text)
            grouped.setdefault(normalized, []).append(signal)
        return grouped

    def _rank_groups(self, grouped: dict[str, list[WorrySignal]]) -> list[RankedWorry]:
        ranked: list[RankedWorry] = []
        for normalized_worry, signals in grouped.items():
            source_diversity = len({signal.source for signal in signals})
            mention_count = len(signals)
            score = sum(signal.weight for signal in signals) + source_diversity * 4 + mention_count * 2
            reasons = []
            if mention_count >= 2:
                reasons.append(f"반복 노출 {mention_count}건")
            if source_diversity >= 2:
                reasons.append(f"출처 다양성 {source_diversity}개")
            if any(signal.signal_type == "trend" for signal in signals):
                reasons.append("트렌드 신호 포함")

            ranked.append(
                RankedWorry(
                    worry=signals[0].text,
                    normalized_worry=normalized_worry,
                    story=_build_worry_story(normalized_worry),
                    score=score,
                    reason=" / ".join(reasons) or "검색형 고민 신호",
                    matched_signals=[signal.text for signal in signals[:8]],
                    supporting_links=_unique_nonempty([signal.url for signal in signals])[:5],
                )
            )

        ranked.sort(key=lambda item: (-item.score, item.normalized_worry))
        return ranked


def save_worries(worries: list[RankedWorry]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "today_worry.json"
    payload = {
        "date": str(date.today()),
        "top_worries": [asdict(worry) for worry in worries],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _normalize_worry(text: str) -> str:
    lowered = text.lower()
    for keywords, normalized in NORMALIZATION_RULES:
        if any(keyword in lowered for keyword in keywords):
            return normalized

    cleaned = _clean_text(text)
    if cleaned.endswith("고민"):
        cleaned = cleaned[:-2].strip()
    if "?" in cleaned:
        cleaned = cleaned.replace("?", "")
    if not any(token in cleaned for token in ("하나", "될까", "되나", "어떡", "어쩌", "맞나")):
        cleaned = f"{cleaned} 어떻게 해야 하나"
    return cleaned


def _build_worry_story(normalized_worry: str) -> list[str]:
    lowered = normalized_worry.lower()

    if any(token in lowered for token in ("답장", "읽씹", "연락", "만나")):
        return [
            "처음엔 바쁜가 보다 하고 넘겼다.",
            "근데 늘 내가 먼저 보내야 대화가 이어진다.",
            "미안하다는 말은 오는데 속도는 안 바뀐다.",
            "이걸 계속 이해해줘야 하나 싶다.",
        ]

    if any(token in lowered for token in ("회사", "퇴사", "이직", "직장")):
        return [
            "일은 하고 있는데 갈수록 내가 줄어드는 느낌이다.",
            "출근 전부터 이미 피곤하고 퇴근하면 아무것도 못 한다.",
            "당장 그만두기엔 불안한데 계속 버티는 것도 맞나 싶다.",
            "참는 게 답인지 정리해야 할 때인지 헷갈린다.",
        ]

    if any(token in lowered for token in ("친구", "손절", "거리")):
        return [
            "예전엔 편했는데 요즘은 만날수록 기분이 무거워진다.",
            "선을 넘는 말이 반복되는데 내가 예민한가 싶어 넘겼다.",
            "억지로 관계를 이어가는 게 맞는지 헷갈린다.",
            "가까운 사이라 더 정리하기 어렵다.",
        ]

    if any(token in lowered for token in ("소비", "절약", "쇼핑", "돈")):
        return [
            "아끼겠다고 마음먹을 때마다 이상하게 더 쓰게 된다.",
            "작은 결제가 쌓여서 나중에 통장을 보면 허무하다.",
            "필요한 소비인지 순간 기분인지 기준이 자꾸 흐려진다.",
            "이번엔 진짜 끊어야 하나 싶다.",
        ]

    if any(token in lowered for token in ("루틴", "습관", "운동", "자기관리")):
        return [
            "시작할 때는 이번엔 다를 것 같았다.",
            "근데 며칠 지나면 금방 흐트러진다.",
            "의지가 약한 건지 방식이 잘못된 건지 모르겠다.",
            "계속 작심삼일이면 뭘 바꿔야 하나 싶다.",
        ]

    return [
        "처음엔 대수롭지 않게 넘겼다.",
        "근데 같은 장면이 반복되기 시작했다.",
        "이걸 계속 이해해야 하나 싶어졌다.",
        "이제는 기준을 정해야 할 것 같다.",
    ]


def _contains_sensitive_keyword(text: str) -> bool:
    return any(token in text for token in SENSITIVE_KEYWORDS)


def _normalize_text(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", text.lower())


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
    logger = setup_logger(Path("logs") / "daily_worry.log")
    collector = DailyWorryCollector(logger=logger)
    worries = collector.collect()
    if not worries:
        raise SystemExit(1)
    output_path = save_worries(worries)
    print(f"daily worry saved: {output_path}")
    print(json.dumps({"top_worries": [asdict(item) for item in worries]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
