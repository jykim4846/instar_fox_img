from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any
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


CAROUSEL_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "daily_carousel_content",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "hook": {"type": "string"},
            "angle": {"type": "string"},
            "slides": {
                "type": "array",
                "minItems": 7,
                "maxItems": 7,
                "items": {
                    "type": "object",
                    "properties": {
                        "eyebrow": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "footer": {"type": "string"},
                        "inverted": {"type": "boolean"},
                    },
                    "required": ["eyebrow", "title", "body", "footer", "inverted"],
                    "additionalProperties": False,
                },
            },
            "caption": {"type": "string"},
            "hashtags": {
                "type": "array",
                "minItems": 6,
                "maxItems": 12,
                "items": {"type": "string"},
            },
        },
        "required": ["hook", "angle", "slides", "caption", "hashtags"],
        "additionalProperties": False,
    },
}


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


def build_openai_carousel_content(
    winner: RankedTrend,
    ranked: list[RankedTrend],
    logger,
) -> DailyCarouselContent | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.info("OPENAI_API_KEY 없음 - 템플릿 작성기로 fallback")
        return None

    try:
        from openai import OpenAI
    except ImportError as error:
        logger.warning("openai 패키지 없음 - 템플릿 작성기로 fallback | %s", error)
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini"
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": _openai_system_prompt()},
                {"role": "user", "content": _openai_user_prompt(winner, ranked)},
            ],
            text={"format": CAROUSEL_SCHEMA},
            max_output_tokens=1800,
        )
        payload = json.loads((response.output_text or "").strip())
        content = _content_from_openai_payload(winner, payload)
        logger.info("OpenAI 캐러셀 원고 생성 성공 | model=%s | topic=%s", model, winner.keyword)
        return content
    except Exception as error:  # noqa: BLE001
        logger.warning("OpenAI 캐러셀 원고 생성 실패 - 템플릿 작성기로 fallback | %s", error)
        return None


def save_content(content: DailyCarouselContent, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "carousel_content.json"
    payload = asdict(content)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _content_from_openai_payload(winner: RankedTrend, payload: dict[str, Any]) -> DailyCarouselContent:
    slides = [
        CarouselSlide(
            eyebrow=_clean_text(str(item["eyebrow"]))[:24],
            title=_normalize_title(str(item["title"])),
            body=[_clean_text(str(line))[:100] for line in item["body"][:4]],
            footer=_clean_text(str(item.get("footer", "")))[:42],
            inverted=bool(item["inverted"]),
        )
        for item in payload["slides"]
    ]
    if len(slides) != 7:
        raise ValueError("slides 는 정확히 7장이어야 합니다.")
    if not any(slide.inverted for slide in slides):
        slides[4] = CarouselSlide(
            eyebrow=slides[4].eyebrow,
            title=slides[4].title,
            body=slides[4].body,
            footer=slides[4].footer,
            inverted=True,
        )
    hashtags = [_format_hashtag(str(tag)) for tag in payload["hashtags"][:12]]
    hashtags = [tag for tag in hashtags if tag != "#"]
    if len(hashtags) < 5:
        hashtags = _hashtags(_infer_category(winner))
    return DailyCarouselContent(
        keyword=winner.keyword,
        hook=_clean_text(str(payload["hook"]))[:80],
        angle=_clean_text(str(payload["angle"]))[:180],
        source=winner.source,
        score=winner.final_score,
        slides=slides,
        caption=_clean_caption(str(payload["caption"]), hashtags),
        hashtags=hashtags,
    )


def _openai_system_prompt() -> str:
    return """
너는 인스타그램 카드뉴스 계정의 한국어 에디터다.
매일 최신 트렌드 1개를 7장 캐러셀로 바꾼다.
목표는 클릭bait가 아니라 저장하고 싶은 찔림이다.

원칙:
- 정치, 범죄, 재난, 사망, 질병, 투자 조언, 혐오, 성적 소재로 확장하지 않는다.
- 후보 데이터에 없는 구체 수치나 사실을 새로 만들지 않는다.
- 자극적인 문장은 쓰되 허위 단정, 공포 조장, 특정 집단 비난은 금지한다.
- 문장은 짧고 강하게 쓴다.
- 각 슬라이드 title은 32자 이내, 줄바꿈 포함 최대 4줄.
- 각 body 문장은 70자 이내.
- 5번 슬라이드는 반전/경고 카드로 inverted=true.
- 출력은 JSON만 한다.

7장 구조:
1 표지: 가장 강한 훅
2 왜 지금 보이는지
3 트렌드 신호
4 핵심 관점
5 반전/경고
6 저장할 체크리스트
7 오늘의 기준과 저장 유도
""".strip()


def _openai_user_prompt(winner: RankedTrend, ranked: list[RankedTrend]) -> str:
    ranking_lines = []
    for index, item in enumerate(ranked[:8], start=1):
        ranking_lines.append(
            f"{index}. {item.keyword} | score={item.final_score} | source={item.source} | "
            f"hook={item.hook} | angle={item.angle} | signals={'; '.join(item.signals[:3])}"
        )
    return f"""
선정된 1위 주제:
- keyword: {winner.keyword}
- score: {winner.final_score}
- source: {winner.source}
- description: {winner.description}
- signals: {'; '.join(winner.signals[:5])}
- baseline_hook: {winner.hook}
- baseline_angle: {winner.angle}

후보 랭킹 참고:
{chr(10).join(ranking_lines)}

브랜드 톤:
- 귀여운 여우 캐릭터 계정이지만 문장은 현실적이고 단정적이다.
- 위로보다 판단 기준을 준다.
- 독자가 "이거 저장해야겠다"라고 느끼는 체크리스트를 선호한다.

JSON 필드:
- hook: 표지에 쓸 핵심 훅
- angle: 캡션과 기록에 남길 한 문장 관점
- slides: 정확히 7개
- caption: 인스타 게시 캡션. 5~8줄 + 질문 1개 + 해시태그 문자열 포함
- hashtags: #으로 시작하는 한국어/영어 해시태그 6~12개
""".strip()


def _normalize_title(text: str) -> str:
    cleaned = _clean_text(text)
    if "\n" in text:
        return "\n".join(_clean_text(line) for line in text.splitlines() if _clean_text(line))[:90]
    return _line_break(cleaned[:80], 14)


def _clean_caption(caption: str, hashtags: list[str]) -> str:
    cleaned = "\n".join(line.rstrip() for line in caption.strip().splitlines() if line.strip())
    hashtag_line = " ".join(hashtags)
    if hashtag_line and hashtag_line not in cleaned:
        cleaned = f"{cleaned}\n\n{hashtag_line}"
    return cleaned[:1800]


def _format_hashtag(value: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch.isalnum() or ch in {"_", "#"})
    if not cleaned:
        return "#"
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return cleaned[:30]


def _clean_text(text: str) -> str:
    return " ".join(text.split())


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
