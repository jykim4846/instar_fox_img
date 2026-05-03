from __future__ import annotations

import json
import os
from typing import Any

from estj_content import ESTJCard, get_today
from daily_trend_ranker import RankedTrend


ESTJ_REEL_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "daily_estj_reel",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "bullets": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"type": "string"},
            },
            "hashtags": {"type": "string"},
        },
        "required": ["title", "bullets", "hashtags"],
        "additionalProperties": False,
    },
}


def build_estj_reel_card(
    winner: RankedTrend | None,
    ranked: list[RankedTrend],
    logger,
) -> ESTJCard:
    if winner is None:
        logger.warning("트렌드 후보 없음 - 정적 ESTJ 라이브러리로 fallback")
        return get_today()

    generated = build_openai_estj_reel_card(winner, ranked, logger)
    if generated is not None:
        return generated
    return build_template_estj_reel_card(winner)


def build_openai_estj_reel_card(
    winner: RankedTrend,
    ranked: list[RankedTrend],
    logger,
) -> ESTJCard | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.info("OPENAI_API_KEY 없음 - ESTJ 릴스 템플릿 작성기로 fallback")
        return None

    try:
        from openai import OpenAI
    except ImportError as error:
        logger.warning("openai 패키지 없음 - ESTJ 릴스 템플릿 작성기로 fallback | %s", error)
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini"
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(winner, ranked)},
            ],
            text={"format": ESTJ_REEL_SCHEMA},
            max_output_tokens=900,
        )
        payload = json.loads((response.output_text or "").strip())
        card = _card_from_payload(payload)
        logger.info("OpenAI ESTJ 릴스 원고 생성 성공 | model=%s | topic=%s", model, winner.keyword)
        return card
    except Exception as error:  # noqa: BLE001
        logger.warning("OpenAI ESTJ 릴스 원고 생성 실패 - 템플릿 작성기로 fallback | %s", error)
        return None


def build_template_estj_reel_card(winner: RankedTrend) -> ESTJCard:
    keyword = winner.keyword
    category = _infer_category(winner)
    title = {
        "ai": "ESTJ가 AI를 쓰는 법",
        "spending": "ESTJ의 소비 기준",
        "media": "ESTJ가 뉴스 요약 볼 때",
        "work": "ESTJ의 일 처리 방식",
        "selfcare": "ESTJ의 자기관리 기준",
        "relationship": "ESTJ가 관계를 볼 때",
        "trend": f"ESTJ가 {keyword}를 보면",
    }[category]
    bullets = {
        "ai": [
            "AI한테 맡길 일과 직접 판단할 일부터 나눔",
            "초안은 맡겨도 최종 기준은 본인이 잡음",
            "답이 그럴듯하면 바로 반례부터 물어봄",
            "도구는 좋아하지만 책임까지 넘기진 않음",
        ],
        "spending": [
            "할인율보다 필요한 이유부터 확인함",
            "장바구니에 넣고 바로 안 삼. 3일 지켜봄",
            "싸게 샀다는 말로 충동구매를 합리화하지 않음",
            "안 사도 괜찮으면 그게 제일 큰 절약임",
        ],
        "media": [
            "요약은 보지만 출처부터 확인함",
            "30초 영상 하나로 결론내는 사람을 제일 불안해함",
            "빠른 이해보다 정확한 판단을 더 믿음",
            "공유하기 전에 한 번 더 검색함",
        ],
        "work": [
            "할 일 많을수록 목록부터 정리함",
            "바쁜 척보다 끝낸 결과를 믿음",
            "회의 길어지면 결론부터 찾음",
            "우선순위 없는 속도는 낭비라고 봄",
        ],
        "selfcare": [
            "루틴도 유지 가능해야 루틴이라고 봄",
            "회복까지 숙제처럼 만들면 바로 수정함",
            "기록은 하되 기록에 끌려다니진 않음",
            "꾸준함은 의지가 아니라 구조라고 믿음",
        ],
        "relationship": [
            "한 번의 답장보다 반복 패턴을 봄",
            "애매하면 혼자 추측하지 않고 기준을 말함",
            "말보다 시간 쓰는 방식을 더 믿음",
            "우선순위는 결국 행동에서 보인다고 생각함",
        ],
        "trend": [
            "유행이라고 바로 따라가진 않음",
            "내 생활에 쓸모 있는지부터 봄",
            "재밌어도 기준 없으면 오래 안 감",
            "따라가기 전에 남길 것과 버릴 것을 나눔",
        ],
    }[category]
    return ESTJCard(title=title, bullets=bullets, hashtags=_hashtags(category))


def _card_from_payload(payload: dict[str, Any]) -> ESTJCard:
    title = _clean_text(str(payload["title"]))[:42]
    bullets = [_clean_text(str(item))[:62] for item in payload["bullets"][:4]]
    hashtags = " ".join(_format_hashtag(tag) for tag in str(payload["hashtags"]).split())[:220]
    if len(bullets) != 4:
        raise ValueError("bullets 는 정확히 4개여야 합니다.")
    if not hashtags:
        hashtags = "#ESTJ #MBTI #ESTJ일상 #오늘의트렌드"
    return ESTJCard(title=title, bullets=bullets, hashtags=hashtags)


def _system_prompt() -> str:
    return """
너는 인스타그램 ESTJ 여우 캐릭터 계정의 릴스 작가다.
최신 트렌드 1개를 ESTJ 관점으로 해석한 15초 릴스 문구를 만든다.

규칙:
- title은 22자 이내가 좋고 최대 32자.
- bullets는 정확히 4개.
- 각 bullet은 34자 이내의 짧은 구어체.
- 귀엽지만 판단 기준이 선명해야 한다.
- 정치, 범죄, 재난, 사망, 질병, 투자 조언, 혐오, 성적 소재로 확장하지 않는다.
- 후보 데이터에 없는 구체 수치나 사실을 새로 만들지 않는다.
- 출력은 JSON만 한다.
""".strip()


def _user_prompt(winner: RankedTrend, ranked: list[RankedTrend]) -> str:
    ranking_lines = []
    for index, item in enumerate(ranked[:6], start=1):
        ranking_lines.append(
            f"{index}. {item.keyword} | score={item.final_score} | hook={item.hook} | angle={item.angle}"
        )
    return f"""
오늘의 1위 트렌드:
- keyword: {winner.keyword}
- score: {winner.final_score}
- source: {winner.source}
- description: {winner.description}
- signals: {'; '.join(winner.signals[:4])}
- hook: {winner.hook}
- angle: {winner.angle}

후보 랭킹:
{chr(10).join(ranking_lines)}

ESTJ 여우 톤:
- 감정 과잉보다 기준
- 위로보다 정리
- 애매한 말 싫어함
- 말보다 행동과 반복 패턴을 믿음
- 마지막 bullet은 저장하고 싶은 기준이면 좋다

hashtags에는 #ESTJ #MBTI #ESTJ일상 #여우리 를 포함하고, 트렌드 관련 해시태그 2~4개를 더한다.
""".strip()


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


def _hashtags(category: str) -> str:
    tags = {
        "ai": "#ESTJ #MBTI #ESTJ일상 #여우리 #AI트렌드 #생성형AI #업무효율",
        "spending": "#ESTJ #MBTI #ESTJ일상 #여우리 #소비트렌드 #절약 #쇼핑습관",
        "media": "#ESTJ #MBTI #ESTJ일상 #여우리 #숏폼 #뉴스소비 #미디어트렌드",
        "work": "#ESTJ #MBTI #ESTJ일상 #여우리 #직장인 #일하는방식 #업무효율",
        "selfcare": "#ESTJ #MBTI #ESTJ일상 #여우리 #자기관리 #루틴 #웰니스",
        "relationship": "#ESTJ #MBTI #ESTJ일상 #여우리 #인간관계 #카톡 #연애고민",
        "trend": "#ESTJ #MBTI #ESTJ일상 #여우리 #오늘의트렌드 #트렌드분석",
    }
    return tags[category]


def _format_hashtag(value: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch.isalnum() or ch in {"_", "#"})
    if not cleaned:
        return ""
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return cleaned


def _clean_text(text: str) -> str:
    return " ".join(text.split())
