from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from carousel_ai_trend_renderer import CarouselSlide


MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ",
]


MBTI_TOPICS = [
    "돈 모으기 잘하는",
    "카톡 답장 빠른",
    "약속 시간 잘 지키는",
    "갓생 사는",
    "야근 잘 견디는",
    "여행 계획 세밀한",
    "옷장 정리 잘하는",
    "운동 꾸준한",
    "인간관계 손절 빠른",
    "상사한테 직언 잘하는",
    "회의에서 결론 잘 짓는",
    "새벽까지 깨어있는",
]


@dataclass(frozen=True)
class MBTIRank:
    rank: int
    mbti: str
    one_liner: str


@dataclass(frozen=True)
class MBTIRankingContent:
    topic: str
    ranks: list[MBTIRank]
    summary: str
    slides: list[CarouselSlide]
    caption: str
    hashtags: list[str]


MBTI_RANKING_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "mbti_ranking",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "ranks": {
                "type": "array",
                "minItems": 16,
                "maxItems": 16,
                "items": {
                    "type": "object",
                    "properties": {
                        "mbti": {"type": "string"},
                        "one_liner": {"type": "string"},
                    },
                    "required": ["mbti", "one_liner"],
                    "additionalProperties": False,
                },
            },
            "summary": {"type": "string"},
            "caption": {"type": "string"},
            "hashtags": {
                "type": "array",
                "minItems": 6,
                "maxItems": 14,
                "items": {"type": "string"},
            },
        },
        "required": ["ranks", "summary", "caption", "hashtags"],
        "additionalProperties": False,
    },
}


def select_topic(recent_topics: set[str]) -> str:
    """가장 오래된 미사용 토픽을 라운드로빈으로 선택."""
    for topic in MBTI_TOPICS:
        if topic not in recent_topics:
            return topic
    return MBTI_TOPICS[0]


def build_mbti_ranking(topic: str, logger) -> MBTIRankingContent:
    generated = build_openai_mbti_ranking(topic, logger)
    if generated is not None:
        return generated
    return build_template_mbti_ranking(topic)


def build_openai_mbti_ranking(topic: str, logger) -> MBTIRankingContent | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.info("OPENAI_API_KEY 없음 - MBTI 랭킹 템플릿 작성기로 fallback")
        return None
    try:
        from openai import OpenAI
    except ImportError as error:
        logger.warning("openai 패키지 없음 - MBTI 랭킹 템플릿 작성기로 fallback | %s", error)
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini"
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(topic)},
            ],
            text={"format": MBTI_RANKING_SCHEMA},
            max_output_tokens=2200,
        )
        payload = json.loads((response.output_text or "").strip())
        content = _content_from_payload(topic, payload, logger)
        logger.info("OpenAI MBTI 랭킹 생성 성공 | model=%s | topic=%s", model, topic)
        return content
    except Exception as error:  # noqa: BLE001
        logger.warning("OpenAI MBTI 랭킹 생성 실패 - 템플릿 작성기로 fallback | %s", error)
        return None


def build_template_mbti_ranking(topic: str) -> MBTIRankingContent:
    ranks = [
        MBTIRank(rank=index, mbti=mbti, one_liner=f"{mbti} 스타일")
        for index, mbti in enumerate(MBTI_TYPES, start=1)
    ]
    summary = "결국 차이는 시스템으로 굴리느냐 즉흥으로 가느냐다."
    hashtags = _format_hashtags([])
    slides = _build_slides(topic, ranks, summary)
    caption = _build_caption(
        "너 몇 위였어?\n댓글에 MBTI 떨궈주면 ESTJ 여우가 한 줄 평 던져줄게 🦊",
        hashtags,
    )
    return MBTIRankingContent(
        topic=topic,
        ranks=ranks,
        summary=summary,
        slides=slides,
        caption=caption,
        hashtags=hashtags,
    )


def save_content(content: MBTIRankingContent, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "mbti_ranking_content.json"
    path.write_text(
        json.dumps(asdict(content), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _content_from_payload(topic: str, payload: dict[str, Any], logger) -> MBTIRankingContent:
    raw_ranks = payload.get("ranks", [])[:16]
    ranks: list[MBTIRank] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_ranks, start=1):
        mbti = str(item.get("mbti", "")).upper().strip()
        if mbti not in MBTI_TYPES or mbti in seen:
            continue
        one_liner = " ".join(str(item.get("one_liner", "")).split())[:70]
        ranks.append(MBTIRank(rank=index, mbti=mbti, one_liner=one_liner or "—"))
        seen.add(mbti)
    if len(ranks) < 16:
        missing = [m for m in MBTI_TYPES if m not in seen]
        logger.warning("MBTI 누락 보강 | missing=%s", missing)
        for mbti in missing:
            ranks.append(MBTIRank(rank=len(ranks) + 1, mbti=mbti, one_liner="—"))
    summary = " ".join(str(payload.get("summary", "")).split())[:120]
    if not summary:
        summary = "결국 차이는 시스템으로 굴리느냐 즉흥으로 가느냐다."
    hashtags = _format_hashtags(payload.get("hashtags", []))
    slides = _build_slides(topic, ranks, summary)
    caption = _build_caption(str(payload.get("caption", "")), hashtags)
    return MBTIRankingContent(
        topic=topic,
        ranks=ranks,
        summary=summary,
        slides=slides,
        caption=caption,
        hashtags=hashtags,
    )


def _build_slides(topic: str, ranks: list[MBTIRank], summary: str) -> list[CarouselSlide]:
    title_topic = topic.strip()

    def line(rank: MBTIRank) -> str:
        return f"{rank.rank}위 {rank.mbti} — {rank.one_liner}"

    return [
        CarouselSlide(
            eyebrow="MBTI RANKING",
            title=f"MBTI별\n{title_topic}\n순위 16",
            body=["🦊 ESTJ 여우의 분석 리포트", "스와이프 →"],
        ),
        CarouselSlide(
            eyebrow="TOP 1-3",
            title=f"{title_topic}\nTOP 3",
            body=[
                f"🏆 1위 {ranks[0].mbti} — {ranks[0].one_liner}",
                f"🥈 2위 {ranks[1].mbti} — {ranks[1].one_liner}",
                f"🥉 3위 {ranks[2].mbti} — {ranks[2].one_liner}",
            ],
        ),
        CarouselSlide(
            eyebrow="RANK 4-6",
            title="중상위권 4~6위",
            body=[line(ranks[3]), line(ranks[4]), line(ranks[5])],
        ),
        CarouselSlide(
            eyebrow="RANK 7-9",
            title="중위권 7~9위",
            body=[line(ranks[6]), line(ranks[7]), line(ranks[8])],
        ),
        CarouselSlide(
            eyebrow="RANK 10-12",
            title="중하위권 10~12위",
            body=[line(ranks[9]), line(ranks[10]), line(ranks[11])],
        ),
        CarouselSlide(
            eyebrow="WARNING 13-15",
            title="위험 신호 13~15위",
            body=[line(ranks[12]), line(ranks[13]), line(ranks[14])],
            inverted=True,
        ),
        CarouselSlide(
            eyebrow="LAST + RULE",
            title=f"🚨 16위 {ranks[15].mbti}",
            body=[
                ranks[15].one_liner,
                "",
                "✦ ESTJ 여우 결론",
                summary,
            ],
            footer="저장하고 친구한테 보여주기",
        ),
    ]


def _system_prompt() -> str:
    return """
너는 인스타그램 ESTJ 여우 캐릭터 계정의 MBTI 랭킹 콘텐츠 작가다.
주어진 주제로 16개 MBTI 타입을 1~16위로 매기고, 각 타입에 한 줄 코멘트를 단다.

원칙:
- 16개 MBTI 모두 정확히 한 번씩 등장. 중복/누락 금지.
- 한 줄 코멘트는 40~60자 한국어. 직설+가벼운 풍자, 위로보다 판단 기준.
- 정치, 종교, 외모, 인종, 성별 비하, 비속어 금지.
- 1~5위는 잘하는 쪽, 11~16위는 못하는 쪽으로 자연스럽게 분포.
- 같은 MBTI를 두 번 쓰지 않는다.
- 출력은 JSON만 한다.

ESTJ 여우 톤:
- 가계부, 엑셀, 자동이체, 가성비, 우선순위 같은 실무 단어 자주 사용
- 비유는 짧고 단정적
- 이모지는 거의 쓰지 않음 (표지/결론은 호출자가 따로 붙임)
""".strip()


def _user_prompt(topic: str) -> str:
    types_line = ", ".join(MBTI_TYPES)
    return f"""
주제: "{topic} MBTI 순위 16"

JSON 필드:
- ranks: 정확히 16개. 배열 인덱스 0번이 1위, 15번이 16위.
  - mbti: 4글자 대문자 MBTI (예: "ISTJ")
  - one_liner: 40~60자 한국어 한 줄 코멘트
- summary: 결론 한 문장. 80자 이내. 1~5위 / 6~10위 / 11~16위 패턴을 압축
- caption: 인스타 캡션 본문. 3~5줄 + 댓글 유도 질문 1개. 해시태그 제외
- hashtags: 6~14개. # 없이 한국어/영어 키워드만 (예: "MBTI", "MBTI순위")

MBTI 16타입: {types_line}
""".strip()


def _format_hashtags(values: list) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        cleaned = "".join(ch for ch in text if ch.isalnum() or ch in {"_", "#"})
        if not cleaned:
            continue
        if not cleaned.startswith("#"):
            cleaned = f"#{cleaned}"
        cleaned = cleaned[:30]
        if cleaned not in out:
            out.append(cleaned)
    base = [
        "#MBTI", "#MBTI순위", "#MBTI랭킹", "#MBTI공감",
        "#MBTI유형", "#MBTI테스트", "#ESTJ", "#ESTJ일상", "#여우리",
    ]
    for tag in base:
        if tag not in out:
            out.append(tag)
    return out[:14]


def _build_caption(text: str, hashtags: list[str]) -> str:
    cleaned = "\n".join(line.rstrip() for line in str(text).strip().splitlines() if line.strip())
    if not cleaned:
        cleaned = "너 몇 위였어?\n댓글에 MBTI 떨궈주면 ESTJ 여우가 한 줄 평 던져줄게 🦊"
    hashtag_line = " ".join(hashtags)
    if hashtag_line and hashtag_line not in cleaned:
        cleaned = f"{cleaned}\n\n{hashtag_line}"
    return cleaned[:1800]
