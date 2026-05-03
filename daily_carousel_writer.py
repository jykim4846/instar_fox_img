from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from carousel_ai_trend_renderer import CarouselSlide
from daily_trend_ranker import RankedTrend


@dataclass(frozen=True)
class DailyCarouselContent:
    keyword: str
    hook: str
    angle: str
    source: str
    score: int
    slides: list[CarouselSlide]
    caption: str
    hashtags: list[str]


def build_carousel_content(winner: RankedTrend) -> DailyCarouselContent:
    category = _infer_category(winner)
    slides = [
        CarouselSlide(
            eyebrow="TODAY'S TREND",
            title=_line_break(winner.hook, 14),
            body=[_subhook_for_category(category)],
        ),
        CarouselSlide(
            eyebrow="WHY NOW",
            title="지금 이 흐름이\n눈에 띄는 이유",
            body=[
                _clean_sentence(winner.description) or winner.keyword,
                f"반복 신호: {', '.join(winner.signals[:2])}",
            ],
        ),
        CarouselSlide(
            eyebrow="SIGNAL",
            title=_signal_title(category),
            body=[
                winner.angle,
                "사람들은 이미 이 변화를 일상 선택 기준으로 받아들이고 있다.",
            ],
        ),
        CarouselSlide(
            eyebrow="POINT",
            title=_point_title(category),
            body=_point_body(category),
        ),
        CarouselSlide(
            eyebrow="WARNING",
            title=_warning_title(category),
            body=_warning_body(category),
            inverted=True,
        ),
        CarouselSlide(
            eyebrow="SAVE THIS",
            title="오늘 써먹을 기준",
            body=_checklist(category),
        ),
        CarouselSlide(
            eyebrow="TODAY'S RULE",
            title=_rule_title(category),
            body=[
                "트렌드는 따라가는 게 아니라",
                "내 기준을 점검하는 재료로 쓰는 게 맞다.",
            ],
            footer="저장해두고 다음 선택 전에 다시 보기",
        ),
    ]
    hashtags = _hashtags(category)
    return DailyCarouselContent(
        keyword=winner.keyword,
        hook=winner.hook,
        angle=winner.angle,
        source=winner.source,
        score=winner.final_score,
        slides=slides,
        caption=_caption(winner, category, hashtags),
        hashtags=hashtags,
    )


def save_content(content: DailyCarouselContent, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "carousel_content.json"
    payload = asdict(content)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _infer_category(winner: RankedTrend) -> str:
    text = " ".join([winner.keyword, winner.hook, winner.angle]).lower()
    if any(token in text for token in ("ai", "챗gpt", "chatgpt", "인공지능", "생성형")):
        return "ai"
    if any(token in text for token in ("뉴스", "숏폼", "릴스", "요약", "30초")):
        return "media"
    if any(token in text for token in ("소비", "쇼핑", "가격", "절약", "구독")):
        return "spending"
    if any(token in text for token in ("업무", "직장", "일", "퇴사", "이직")):
        return "work"
    if any(token in text for token in ("루틴", "쉬", "수면", "운동", "자기관리")):
        return "selfcare"
    if any(token in text for token in ("관계", "답장", "카톡", "연애")):
        return "relationship"
    return "trend"


def _subhook_for_category(category: str) -> str:
    return {
        "ai": "이미 다들 조용히 쓰고 있다.",
        "spending": "할인보다 무서운 건 합리화다.",
        "media": "짧아진 건 관심이 아니라 확인 시간이다.",
        "work": "성과는 오래 앉아 있는 순서로 나지 않는다.",
        "selfcare": "회복까지 성과표가 되면 더 지친다.",
        "relationship": "느린 답장보다 애매한 기준이 더 오래 간다.",
        "trend": "유행은 취향보다 먼저 생활을 바꾼다.",
    }[category]


def _signal_title(category: str) -> str:
    return {
        "ai": "AI는 이제\n검색창처럼 쓰인다",
        "spending": "소비는 이제\n정보전이 됐다",
        "media": "뉴스는 점점\n짧게 먼저 들어온다",
        "work": "일의 기준이\n속도와 정리로 옮겨간다",
        "selfcare": "쉬는 방식도\n관리 대상이 됐다",
        "relationship": "관계도 이제\n응답 속도로 해석된다",
        "trend": "반복되는 키워드는\n생활 신호다",
    }[category]


def _point_title(category: str) -> str:
    return {
        "ai": "진짜 차이는\nAI를 쓰느냐가 아니다",
        "spending": "진짜 차이는\n얼마나 싸게 샀느냐가 아니다",
        "media": "진짜 차이는\n빨리 봤느냐가 아니다",
        "work": "진짜 차이는\n얼마나 바빴느냐가 아니다",
        "selfcare": "진짜 차이는\n얼마나 관리했느냐가 아니다",
        "relationship": "진짜 차이는\n답장이 몇 분 늦었느냐가 아니다",
        "trend": "진짜 차이는\n유행을 탔느냐가 아니다",
    }[category]


def _point_body(category: str) -> list[str]:
    return {
        "ai": ["같은 시간 안에", "누가 더 많이 시도하고", "누가 더 빨리 걸러내느냐다."],
        "spending": ["필요한 소비인지", "순간 기분인지", "구매 전에 구분하는 힘이다."],
        "media": ["요약을 봤는지가 아니라", "그 요약을 결론으로 착각하지 않는 힘이다."],
        "work": ["해야 할 일을 늘리는 게 아니라", "안 해도 되는 일을 빨리 지우는 힘이다."],
        "selfcare": ["루틴을 많이 하는 게 아니라", "나를 덜 망가뜨리는 방식을 찾는 힘이다."],
        "relationship": ["상대의 속도를 맞히는 게 아니라", "내 기준을 설명할 수 있는 힘이다."],
        "trend": ["따라가는 속도가 아니라", "내 생활에 남길지 거를지 정하는 힘이다."],
    }[category]


def _warning_title(category: str) -> str:
    return {
        "ai": "생각까지 맡기면\n그때부터 위험하다",
        "spending": "싸게 샀다는 말이\n필요했다는 뜻은 아니다",
        "media": "30초 요약은\n결론이 아니라 입구다",
        "work": "바쁨은\n성과의 증거가 아니다",
        "selfcare": "회복까지 숙제가 되면\n쉬어도 지친다",
        "relationship": "답장 속도만 보면\n사람을 잘못 읽는다",
        "trend": "자극적인 유행은\n기준을 흐리게 만든다",
    }[category]


def _warning_body(category: str) -> list[str]:
    return {
        "ai": ["AI는 답을 주는 도구가 아니라", "생각의 재료를 압축해주는 도구다.", "판단까지 넘기면 기준이 사라진다."],
        "spending": ["최저가는 필요 없는 물건도", "합리적인 선택처럼 보이게 만든다.", "싼 가격보다 중요한 건 안 샀어도 괜찮았는지다."],
        "media": ["짧은 정보는 편하지만", "짧은 확신까지 같이 만든다.", "빠른 이해와 정확한 판단은 다르다."],
        "work": ["계속 바쁜 상태는", "중요한 일을 하고 있다는 뜻이 아니다.", "우선순위가 없으면 속도도 낭비된다."],
        "selfcare": ["수면, 운동, 식단까지 점수가 되면", "회복도 또 하나의 업무가 된다.", "관리보다 먼저 기준이 필요하다."],
        "relationship": ["느린 답장은 신호일 수 있지만", "그 자체가 결론은 아니다.", "패턴과 대화를 같이 봐야 한다."],
        "trend": ["반응이 큰 주제일수록", "과장이 섞이기 쉽다.", "따라가기 전에 내 기준으로 번역해야 한다."],
    }[category]


def _checklist(category: str) -> list[str]:
    return {
        "ai": ["반복 작업인가?", "판단이 필요한 일인가?", "반례를 물어봤나?", "최종 기준은 내가 세웠나?"],
        "spending": ["안 샀어도 괜찮았나?", "가격 때문에 끌린 건 아닌가?", "대체재가 이미 있나?", "내일도 필요할까?"],
        "media": ["출처를 확인했나?", "반대 관점도 봤나?", "요약과 사실을 구분했나?", "공유 전 멈췄나?"],
        "work": ["이 일이 목표와 연결되나?", "안 해도 되는 일인가?", "위임할 수 있나?", "오늘 끝낼 기준이 있나?"],
        "selfcare": ["나에게 맞는 속도인가?", "유지 가능한가?", "회복이 목적 맞나?", "비교 때문에 하는 건 아닌가?"],
        "relationship": ["한 번의 반응인가?", "반복 패턴인가?", "내 기준을 말했나?", "혼자 결론낸 건 아닌가?"],
        "trend": ["내 생활과 관련 있나?", "하루 지나도 의미 있나?", "출처가 분명한가?", "저장할 기준이 있나?"],
    }[category]


def _rule_title(category: str) -> str:
    return {
        "ai": "AI에게 맡길 것과\n내가 판단할 것을\n먼저 나눠라",
        "spending": "싸게 사기 전에\n안 사도 되는지\n먼저 물어라",
        "media": "빨리 보기 전에\n맞는 말인지\n먼저 확인해라",
        "work": "더 하기 전에\n덜어낼 일을\n먼저 정해라",
        "selfcare": "관리하기 전에\n회복할 기준을\n먼저 정해라",
        "relationship": "반응을 해석하기 전에\n내 기준을\n먼저 말해라",
        "trend": "따라가기 전에\n내 생활에 남길지\n먼저 정해라",
    }[category]


def _caption(winner: RankedTrend, category: str, hashtags: list[str]) -> str:
    return "\n".join(
        [
            winner.hook,
            "",
            winner.angle,
            "",
            "중요한 건 트렌드를 빨리 따라가는 게 아니라",
            "그 흐름이 내 생활의 어떤 기준을 바꾸는지 보는 것이다.",
            "",
            "오늘 이 주제, 당신은 어떻게 보고 있나요?",
            "",
            " ".join(hashtags),
        ]
    )


def _hashtags(category: str) -> list[str]:
    base = ["#카드뉴스", "#오늘의트렌드", "#트렌드분석", "#일상인사이트", "#여우리"]
    category_tags = {
        "ai": ["#AI트렌드", "#생성형AI", "#업무효율"],
        "spending": ["#소비트렌드", "#절약", "#쇼핑습관"],
        "media": ["#숏폼", "#뉴스소비", "#미디어트렌드"],
        "work": ["#직장인", "#업무효율", "#일하는방식"],
        "selfcare": ["#자기관리", "#루틴", "#웰니스"],
        "relationship": ["#인간관계", "#연애고민", "#카톡"],
        "trend": ["#트렌드", "#라이프스타일", "#인사이트"],
    }
    return category_tags[category] + base


def _line_break(text: str, max_chars: int) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= max_chars:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return "\n".join(lines[:4])


def _clean_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:90]
