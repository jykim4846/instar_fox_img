from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal, Protocol


class TrendCandidate(Protocol):
    keyword: str
    source: str


Category = Literal["selfcare", "work", "dating", "spending", "trend", "lifestyle"]

SENSITIVE_KEYWORDS = {
    "정치",
    "대선",
    "총선",
    "선거",
    "국회",
    "대통령",
    "탄핵",
    "전쟁",
    "폭격",
    "재난",
    "지진",
    "산불",
    "홍수",
    "범죄",
    "살인",
    "사망",
    "부고",
    "폭락",
    "급락",
    "주가",
    "코인",
    "성폭행",
    "혐오",
    "차별",
    "야동",
    "성인",
    "19금",
}

APP_SERVICE_KEYWORDS = {
    "앱",
    "어플",
    "서비스",
    "구독",
    "알림",
    "업데이트",
    "인스타",
    "릴스",
    "노션",
    "카톡",
    "카카오톡",
    "챗gpt",
    "chatgpt",
    "유튜브",
    "넷플릭스",
    "쿠팡",
    "배달",
}

MISLEADING_KEYWORDS = {
    "소비에트",
    "소비뇽",
    "영어로",
    "영단어",
    "번역",
    "홍혜주",
    "연방",
    "의 뜻",
    "뜻",
    "meaning",
}

MEDICAL_OR_REFERENCE_KEYWORDS = {
    "유산",
    "탈구",
    "증상",
    "진단",
    "치료",
    "질환",
    "병원",
    "약",
    "복용",
    "수술",
    "염증",
    "통증",
    "검사",
    "질병",
    "의학",
    "사전",
    "백과",
    "위키",
}

CATEGORY_STRICT_TOKENS = {
    "소비",
    "연애",
    "직장",
    "회사",
    "앱",
    "서비스",
}

TRENDY_LIFESTYLE_KEYWORDS = {
    "무지출",
    "챌린지",
    "릴스",
    "밈",
    "쇼츠",
    "구독",
    "알림",
    "업데이트",
    "퇴근",
    "출근",
    "직장인",
    "루틴",
    "카톡",
    "읽씹",
    "배달",
    "다이소",
    "쿠팡",
    "올영",
    "텀블러",
    "스레드",
}

CATEGORY_RULES: list[tuple[Category, tuple[str, ...], str, int]] = [
    (
        "selfcare",
        ("루틴", "수면", "운동", "식단", "자기관리", "아침", "영양제", "갓생", "습관"),
        "시작보다 유지가 어려운 자기관리 포인트로 비튼다",
        100,
    ),
    (
        "spending",
        ("소비", "세일", "할인", "쿠폰", "가성비", "무지출", "쇼핑", "공구", "결제"),
        "필요와 충동구매를 가르는 소비 기준으로 비튼다",
        100,
    ),
    (
        "work",
        ("직장", "회사", "출근", "퇴근", "회의", "보고", "메일", "야근", "이직", "업무"),
        "바빠 보이는 것과 효율적인 것을 구분하는 직장 포인트로 비튼다",
        100,
    ),
    (
        "dating",
        ("연애", "소개팅", "썸", "데이트", "읽씹", "카톡", "고백"),
        "말보다 행동 기준이 보이는 연애 포인트로 비튼다",
        100,
    ),
    (
        "trend",
        ("챌린지", "밈", "유행", "테스트", "짤", "숏폼", "화제"),
        "가볍게 따라가지만 오래 못 가는 유행 패턴으로 비튼다",
        95,
    ),
]


@dataclass(frozen=True)
class FilteredTopic:
    keyword: str
    topic: str
    category: Category
    angle: str
    source: str
    priority: int


def filter_topics(
    candidates: list[TrendCandidate],
    max_topics: int,
    logger: logging.Logger,
) -> list[FilteredTopic]:
    logger.info("주제 필터링 시작 | 입력 %s개", len(candidates))
    filtered: list[FilteredTopic] = []
    seen: set[str] = set()

    for candidate in candidates:
        topic = classify_topic(candidate)
        if topic is None:
            continue

        normalized = _normalize(topic.topic)
        if normalized in seen:
            continue

        seen.add(normalized)
        filtered.append(topic)

    filtered.sort(key=lambda item: (-item.priority, item.topic))
    selected = filtered[:max_topics]
    if selected:
        logger.info(
            "선정 주제 샘플 | %s",
            ", ".join(item.topic for item in selected[:5]),
        )
    logger.info("주제 필터링 종료 | 출력 %s개", len(selected))
    return selected


def classify_topic(candidate: TrendCandidate) -> FilteredTopic | None:
    keyword = candidate.keyword.strip()
    lowered = keyword.lower()

    if not keyword or _contains_sensitive_keyword(lowered):
        return None
    if _contains_misleading_keyword(lowered):
        return None
    if _looks_like_medical_or_reference_term(lowered):
        return None
    if _looks_too_specific(lowered):
        return None

    for category, keywords, angle, priority in CATEGORY_RULES:
        if any(_matches_keyword(lowered, token) for token in keywords):
            return FilteredTopic(
                keyword=keyword,
                topic=_generalize_topic(keyword),
                category=category,
                angle=angle,
                source=candidate.source,
                priority=priority + _priority_bonus(lowered),
            )

    if any(_matches_keyword(lowered, token) for token in APP_SERVICE_KEYWORDS):
        return FilteredTopic(
            keyword=keyword,
            topic=_generalize_topic(keyword),
            category="lifestyle",
            angle="앱과 서비스 사용 문화에서 생기는 생활 습관 포인트로 비튼다",
            source=candidate.source,
            priority=90 + _priority_bonus(lowered),
        )

    if _is_generic_lifestyle_keyword(lowered):
        return FilteredTopic(
            keyword=keyword,
            topic=_generalize_topic(keyword),
            category="trend",
            angle="일상 공감으로 바꾸기 쉬운 유행 키워드 관점으로 비튼다",
            source=candidate.source,
            priority=80 + _priority_bonus(lowered),
        )

    return None


def _contains_sensitive_keyword(lowered_keyword: str) -> bool:
    return any(token in lowered_keyword for token in SENSITIVE_KEYWORDS)


def _contains_misleading_keyword(lowered_keyword: str) -> bool:
    return any(token in lowered_keyword for token in MISLEADING_KEYWORDS)


def _looks_like_medical_or_reference_term(lowered_keyword: str) -> bool:
    if any(token in lowered_keyword for token in MEDICAL_OR_REFERENCE_KEYWORDS):
        return True

    medical_prefixes = ("습관성", "급성", "만성")
    if any(lowered_keyword.startswith(prefix) for prefix in medical_prefixes):
        return True

    return False


def _looks_too_specific(lowered_keyword: str) -> bool:
    if re.fullmatch(r"[A-Z0-9\s\-]+", lowered_keyword.upper()) and lowered_keyword not in {
        "chatgpt",
    }:
        return True

    words = re.findall(r"[가-힣a-z0-9]+", lowered_keyword)
    if len(words) >= 4 and not any(token in lowered_keyword for token in APP_SERVICE_KEYWORDS):
        return True

    if re.search(r"\bvs\b", lowered_keyword):
        return True

    return False


def _is_generic_lifestyle_keyword(lowered_keyword: str) -> bool:
    generic_tokens = (
        "봄",
        "여름",
        "가을",
        "겨울",
        "커피",
        "출근룩",
        "도시락",
        "정리",
        "공부",
        "산책",
        "다꾸",
        "집꾸",
        "브이로그",
        "플리",
        "ootd",
    )
    return any(token in lowered_keyword for token in generic_tokens)


def _generalize_topic(keyword: str) -> str:
    cleaned = re.sub(r"\s+", " ", keyword).strip()
    return cleaned[:40]


def _matches_keyword(lowered_keyword: str, token: str) -> bool:
    if token not in lowered_keyword:
        return False

    if token in CATEGORY_STRICT_TOKENS:
        pattern = rf"(^|[^0-9a-z가-힣]){re.escape(token)}([^0-9a-z가-힣]|$)"
        return re.search(pattern, lowered_keyword) is not None

    return True


def _priority_bonus(lowered_keyword: str) -> int:
    return sum(5 for token in TRENDY_LIFESTYLE_KEYWORDS if token in lowered_keyword)


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", value.lower())
