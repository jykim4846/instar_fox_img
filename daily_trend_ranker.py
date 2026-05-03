from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from topic_filter import SENSITIVE_KEYWORDS
from trend_collector import GOOGLE_NEWS_RSS_URLS, USER_AGENT, fetch_trending_keywords


DEFAULT_OUTPUT_DIR = Path("output") / "daily_carousel"

HIGH_FIT_KEYWORDS = {
    "ai",
    "챗gpt",
    "chatgpt",
    "생성형",
    "인공지능",
    "업무",
    "직장",
    "퇴사",
    "이직",
    "소비",
    "쇼핑",
    "절약",
    "가격",
    "구독",
    "숏폼",
    "릴스",
    "뉴스",
    "요약",
    "루틴",
    "수면",
    "운동",
    "자기관리",
    "연애",
    "관계",
    "카톡",
}

HOOK_KEYWORDS = {
    "ai",
    "챗gpt",
    "chatgpt",
    "소비",
    "쇼핑",
    "가격",
    "구독",
    "업무",
    "직장",
    "뉴스",
    "숏폼",
    "루틴",
    "연애",
    "카톡",
}

EVERGREEN_KEYWORDS = {
    "ai",
    "인공지능",
    "업무",
    "소비",
    "쇼핑",
    "절약",
    "루틴",
    "자기관리",
    "관계",
    "뉴스",
    "숏폼",
    "구독",
}

HARD_EXCLUDE_KEYWORDS = SENSITIVE_KEYWORDS | {
    "정당",
    "검찰",
    "법원",
    "소송",
    "체포",
    "구속",
    "피살",
    "사고",
    "감염",
    "암",
    "백신",
    "주식",
    "투자",
    "추천주",
}

FACT_RISK_KEYWORDS = {
    "논란",
    "논쟁",
    "의혹",
    "폭로",
    "루머",
    "단독",
    "충격",
    "파문",
    "급등",
    "폭락",
}

SUGGEST_SEEDS = (
    "AI 업무",
    "AI 쇼핑",
    "생성형 AI",
    "숏폼 뉴스",
    "직장인 고민",
    "소비 트렌드",
    "구독 서비스",
    "자기관리 루틴",
    "카톡 답장",
    "돈 모으기",
)


@dataclass(frozen=True)
class TrendCandidate:
    keyword: str
    source: str
    description: str
    trend_strength: int
    signals: list[str]


@dataclass(frozen=True)
class RankedTrend:
    keyword: str
    source: str
    description: str
    signals: list[str]
    trend_strength: int
    audience_fit: int
    hook_potential: int
    evergreen_value: int
    source_diversity: int
    sensitivity_risk: int
    factual_risk: int
    brand_mismatch: int
    final_score: int
    angle: str
    hook: str


def collect_ranked_trends(logger, limit: int = 12) -> list[RankedTrend]:
    candidates = collect_trend_candidates(logger)
    grouped = _group_candidates(candidates)
    ranked = [score_candidate(keyword, items) for keyword, items in grouped.items()]
    ranked = [item for item in ranked if item.sensitivity_risk < 8 and item.final_score > 0]
    ranked.sort(key=lambda item: (-item.final_score, item.keyword))
    return ranked[:limit]


def collect_trend_candidates(logger) -> list[TrendCandidate]:
    candidates: list[TrendCandidate] = []
    candidates.extend(_collect_google_trends(logger))
    candidates.extend(_collect_google_news(logger))
    candidates.extend(_collect_google_suggest(logger))
    return candidates


def score_candidate(keyword: str, candidates: list[TrendCandidate]) -> RankedTrend:
    combined = " ".join([keyword, *[candidate.description for candidate in candidates]]).lower()
    sources = {candidate.source for candidate in candidates}
    trend_strength = min(10, max(candidate.trend_strength for candidate in candidates) + len(candidates) // 2)
    audience_fit = _score_keyword_overlap(combined, HIGH_FIT_KEYWORDS)
    hook_potential = _score_keyword_overlap(combined, HOOK_KEYWORDS)
    evergreen_value = _score_keyword_overlap(combined, EVERGREEN_KEYWORDS)
    source_diversity = min(10, len(sources) * 3)
    sensitivity_risk = _risk_score(combined, HARD_EXCLUDE_KEYWORDS)
    factual_risk = _risk_score(combined, FACT_RISK_KEYWORDS)
    brand_mismatch = _brand_mismatch_score(combined)

    final_score = (
        trend_strength * 30
        + audience_fit * 25
        + hook_potential * 20
        + evergreen_value * 15
        + source_diversity * 10
        - sensitivity_risk * 40
        - factual_risk * 30
        - brand_mismatch * 25
    )

    category = _infer_category(combined)
    return RankedTrend(
        keyword=keyword,
        source=" / ".join(sorted(sources)),
        description=_first_nonempty([candidate.description for candidate in candidates]),
        signals=_unique([signal for candidate in candidates for signal in candidate.signals])[:8],
        trend_strength=trend_strength,
        audience_fit=audience_fit,
        hook_potential=hook_potential,
        evergreen_value=evergreen_value,
        source_diversity=source_diversity,
        sensitivity_risk=sensitivity_risk,
        factual_risk=factual_risk,
        brand_mismatch=brand_mismatch,
        final_score=final_score,
        angle=_angle_for_category(category, keyword),
        hook=_hook_for_category(category, keyword),
    )


def save_ranking(ranked: list[RankedTrend], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "ranking.json"
    payload = {"ranked_trends": [asdict(item) for item in ranked]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _collect_google_trends(logger) -> list[TrendCandidate]:
    candidates: list[TrendCandidate] = []
    for item in fetch_trending_keywords(limit=20, logger=logger):
        if _is_excluded(item.keyword):
            continue
        strength = min(10, max(4, item.traffic_num // 50000))
        candidates.append(
            TrendCandidate(
                keyword=_clean_keyword(item.keyword),
                source="Google Trends",
                description=item.description,
                trend_strength=strength,
                signals=[f"검색량 {item.traffic}", item.description],
            )
        )
    return candidates


def _collect_google_news(logger) -> list[TrendCandidate]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    candidates: list[TrendCandidate] = []
    for url in GOOGLE_NEWS_RSS_URLS:
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except Exception as error:  # noqa: BLE001
            logger.warning("Google News RSS 수집 실패 | %s | %s", url, error)
            continue
        for item in root.findall(".//item")[:30]:
            raw_title = _clean_html(item.findtext("title", "")).strip()
            if not raw_title:
                continue
            title, source = _split_news_title(raw_title)
            keyword = _news_keyword(title)
            if not keyword or _is_excluded(keyword):
                continue
            candidates.append(
                TrendCandidate(
                    keyword=keyword,
                    source=f"Google News:{source or 'unknown'}",
                    description=title,
                    trend_strength=5,
                    signals=[title],
                )
            )
    return candidates


def _collect_google_suggest(logger) -> list[TrendCandidate]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    candidates: list[TrendCandidate] = []
    for seed in SUGGEST_SEEDS:
        try:
            response = session.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "hl": "ko", "gl": "kr", "q": seed},
                timeout=15,
            )
            response.raise_for_status()
            payload = json.loads(response.text)
        except Exception as error:  # noqa: BLE001
            logger.warning("Google Suggest 수집 실패 | %s | %s", seed, error)
            continue
        suggestions = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        for suggestion in suggestions[:8]:
            keyword = _clean_keyword(str(suggestion))
            if not keyword or _is_excluded(keyword):
                continue
            candidates.append(
                TrendCandidate(
                    keyword=keyword,
                    source=f"Google Suggest:{seed}",
                    description=f"{seed} 연관 검색어",
                    trend_strength=4,
                    signals=[f"{seed} 연관 검색어"],
                )
            )
    return candidates


def _group_candidates(candidates: list[TrendCandidate]) -> dict[str, list[TrendCandidate]]:
    grouped: dict[str, list[TrendCandidate]] = {}
    for candidate in candidates:
        key = _canonical_keyword(candidate.keyword)
        if not key:
            continue
        grouped.setdefault(key, []).append(candidate)
    return grouped


def _canonical_keyword(keyword: str) -> str:
    lowered = keyword.lower()
    if any(token in lowered for token in ("ai", "챗gpt", "chatgpt", "인공지능", "생성형")):
        return "AI 일상화"
    if any(token in lowered for token in ("숏폼", "릴스", "쇼츠", "뉴스", "요약")):
        return "숏폼 뉴스 소비"
    if any(token in lowered for token in ("쇼핑", "가격", "소비", "절약", "구독")):
        return "똑똑한 소비"
    if any(token in lowered for token in ("직장", "업무", "퇴사", "이직", "출근")):
        return "일하는 방식 변화"
    if any(token in lowered for token in ("루틴", "수면", "운동", "자기관리")):
        return "성과가 된 자기관리"
    if any(token in lowered for token in ("연애", "카톡", "답장", "관계")):
        return "관계의 속도감"
    cleaned = _clean_keyword(keyword)
    return cleaned[:30]


def _infer_category(text: str) -> str:
    if any(token in text for token in ("ai", "챗gpt", "chatgpt", "인공지능", "생성형")):
        return "ai"
    if any(token in text for token in ("숏폼", "릴스", "쇼츠", "뉴스", "요약")):
        return "media"
    if any(token in text for token in ("쇼핑", "가격", "소비", "절약", "구독")):
        return "spending"
    if any(token in text for token in ("직장", "업무", "퇴사", "이직", "출근")):
        return "work"
    if any(token in text for token in ("루틴", "수면", "운동", "자기관리")):
        return "selfcare"
    if any(token in text for token in ("연애", "카톡", "답장", "관계")):
        return "relationship"
    return "trend"


def _hook_for_category(category: str, keyword: str) -> str:
    hooks = {
        "ai": "AI 안 쓰는 사람이 더 이상 신중한 사람이 아닐 수 있다",
        "spending": "이제 싸게 사는 사람보다 덜 속는 사람이 이긴다",
        "media": "뉴스를 안 보는 게 아니라 30초로 보는 거다",
        "work": "열심히 일하는 사람보다 빨리 정리하는 사람이 이긴다",
        "selfcare": "쉬는 것도 성과가 된 시대가 왔다",
        "relationship": "답장이 느린 게 문제가 아니라 기준이 없는 게 문제다",
        "trend": f"{keyword}, 그냥 유행이 아니라 생활 방식의 신호다",
    }
    return hooks.get(category, hooks["trend"])


def _angle_for_category(category: str, keyword: str) -> str:
    angles = {
        "ai": "AI가 선택지가 아니라 일상 도구가 되면서 일의 속도와 판단 기준이 갈라지고 있다.",
        "spending": "가격 비교와 추천 알고리즘이 소비를 똑똑하게 만들지만 필요 없는 소비도 합리적으로 보이게 만든다.",
        "media": "짧은 요약이 뉴스 접근성을 높이지만 빠른 확신도 함께 만든다.",
        "work": "업무량보다 정리 속도와 우선순위 판단이 생산성의 기준이 되고 있다.",
        "selfcare": "회복과 루틴까지 관리 대상이 되면서 쉼도 성과처럼 소비되고 있다.",
        "relationship": "메시지 속도와 반응성이 관계의 안정감을 판단하는 기준처럼 쓰이고 있다.",
        "trend": f"{keyword}가 반복 노출되는 이유는 일상 선택 기준이 바뀌고 있기 때문이다.",
    }
    return angles.get(category, angles["trend"])


def _score_keyword_overlap(text: str, keywords: set[str]) -> int:
    hits = sum(1 for keyword in keywords if keyword in text)
    return min(10, hits * 2)


def _risk_score(text: str, keywords: set[str]) -> int:
    hits = sum(1 for keyword in keywords if keyword in text)
    return min(10, hits * 3)


def _brand_mismatch_score(text: str) -> int:
    if re.search(r"[가-힣]", text) is None:
        return 8
    if len(text) > 120:
        return 4
    return 0


def _is_excluded(keyword: str) -> bool:
    lowered = keyword.lower()
    return any(token in lowered for token in HARD_EXCLUDE_KEYWORDS)


def _news_keyword(title: str) -> str:
    cleaned = re.sub(r"[\[\]\"'“”‘’]", "", title)
    words = re.findall(r"[0-9a-zA-Z가-힣]+", cleaned)
    if not words:
        return ""
    return " ".join(words[:4])


def _split_news_title(raw_title: str) -> tuple[str, str]:
    if " - " in raw_title:
        title, source = raw_title.rsplit(" - ", 1)
        return title.strip(), source.strip()
    return raw_title.strip(), ""


def _clean_keyword(value: str) -> str:
    return " ".join(value.split()).strip()


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def _first_nonempty(values: list[str]) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return ""


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean_keyword(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result
