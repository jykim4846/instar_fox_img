from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from openai import OpenAI

from config import Settings
from topic_filter import FilteredTopic


Category = Literal["selfcare", "work", "dating", "spending", "trend", "lifestyle"]
CutType = Literal["dialogue", "narration", "fact"]
SpeakerType = Literal["fox", "me", "other", "none"]


@dataclass(frozen=True)
class VisualSelection:
    background: str = ""
    cut1: str = ""
    cut2: str = ""
    cut3: str = ""
    cut4: str = ""
    cut5: str = ""
    cut6: str = ""


@dataclass(frozen=True)
class CutLine:
    type: CutType
    speaker: SpeakerType
    text: str


CONTENT_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "estj_fox_content",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "topic": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["selfcare", "work", "dating", "spending", "trend", "lifestyle"],
            },
            "template_type": {"type": "string", "enum": ["webtoon_6"]},
            "cuts": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["dialogue", "narration", "fact"]},
                        "speaker": {"type": "string", "enum": ["fox", "me", "other", "none"]},
                        "text": {"type": "string"},
                    },
                    "required": ["type", "speaker", "text"],
                    "additionalProperties": False,
                },
            },
            "caption": {"type": "string"},
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "visuals": {
                "type": "object",
                "properties": {
                    "background": {"type": "string"},
                    "cut1": {"type": "string"},
                    "cut2": {"type": "string"},
                    "cut3": {"type": "string"},
                    "cut4": {"type": "string"},
                    "cut5": {"type": "string"},
                    "cut6": {"type": "string"},
                },
                "required": ["background", "cut1", "cut2", "cut3", "cut4", "cut5", "cut6"],
                "additionalProperties": False,
            },
        },
        "required": [
            "title",
            "topic",
            "category",
            "template_type",
            "cuts",
            "caption",
            "hashtags",
            "visuals",
        ],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class GeneratedContent:
    title: str
    topic: str
    category: Category
    template_type: str
    cuts: list[CutLine]
    caption: str
    hashtags: list[str]
    visuals: VisualSelection = field(default_factory=VisualSelection)

    @property
    def cut1(self) -> str:
        return self.cuts[0].text

    @property
    def cut2(self) -> str:
        return self.cuts[1].text

    @property
    def cut3(self) -> str:
        return self.cuts[2].text

    @property
    def cut4(self) -> str:
        return self.cuts[3].text

    @property
    def cut5(self) -> str:
        return self.cuts[4].text

    @property
    def cut6(self) -> str:
        return self.cuts[5].text


class ContentGenerator:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, topic: FilteredTopic) -> GeneratedContent | None:
        for attempt in range(1, self.settings.openai_retry_attempts + 1):
            try:
                response = self.client.responses.create(
                    model=self.settings.openai_model,
                    input=[
                        {"role": "system", "content": build_system_prompt()},
                        {"role": "user", "content": build_user_prompt(topic)},
                    ],
                    text={"format": CONTENT_SCHEMA},
                    max_output_tokens=900,
                )

                raw_json = (response.output_text or "").strip()
                if not raw_json:
                    raise ValueError("OpenAI 응답이 비어 있습니다.")

                payload = json.loads(raw_json)
                content = validate_generated_content(payload, expected_topic=topic)
                self.logger.info("콘텐츠 생성 성공 | topic=%s | attempt=%s", topic.topic, attempt)
                return content
            except Exception as error:  # noqa: BLE001
                self.logger.warning(
                    "콘텐츠 생성 실패 | topic=%s | attempt=%s | %s",
                    topic.topic,
                    attempt,
                    error,
                )

        self.logger.error("콘텐츠 생성 최종 실패 | topic=%s", topic.topic)
        return None


def build_system_prompt() -> str:
    return """
너는 인스타 캐릭터 계정 estj_fox의 전속 콘텐츠 작가다.
캐릭터는 귀여운 사막여우지만 말투는 ESTJ처럼 현실적이고 단정적이다.
짧고 저장하고 싶은 문장을 만든다.
감정 과장, 위로형 문장, 블로그체, 설명체를 금지한다.
정치, 범죄, 혐오, 재난, 성적 주제를 다루지 않는다.
출력은 반드시 JSON만 한다.
6컷 웹툰 구조로 쓴다.
""".strip()


def build_user_prompt(topic: FilteredTopic) -> str:
    return f"""
topic: {topic.topic}
raw_keyword: {topic.keyword}
recommended_category: {topic.category}
angle: {topic.angle}

규칙:
- 총 6컷
- 1컷: 상황 시작
- 2컷: 상황 확대
- 3컷: 공감 포인트
- 4컷: 자기합리화/전개
- 5컷: 흐름 전환
- 6컷: 여우리의 팩트 한마디
- 각 컷은 짧게
- 마지막 컷은 가장 강하게
- 대화형 장면이 우선이다
- 가능한 컷 1~4는 대화나 속말로 진행한다
- 컷 6은 가능하면 speaker 가 fox 여야 한다

추가 규칙:
- JSON만 출력
- 모든 텍스트는 한국어
- topic 값은 "{topic.topic}" 유지
- category 값은 "{topic.category}" 유지
- template_type 은 반드시 "webtoon_6"
- title 은 저장하고 싶은 한마디처럼 짧고 선명해야 함
- 설명하지 말고 장면으로 써라
- 위로하지 말고 정리해라
- 명언체, 교훈체, 블로그체 금지
- raw_keyword 가 왜 지금 보이는지 생활 장면이 느껴져야 함
- 각 컷은 가능하면 18자 내외
- 해시태그는 정확히 3개
- visuals 파일명은 아래 후보 중 어울리는 것을 고를 것
- 배경 후보: blank.png, office.png, home.png, bed.png, chat.png, shopping.png
- 여우 후보: neutral_front.png, annoyed.png, judging.png, arms_crossed.png, pointing.png, phone_looking.png, lying_down.png, sitting_blank.png, closeup_face.png, tiny_icon.png

출력 스키마:
{{
  "title": "문자열",
  "topic": "문자열",
  "category": "dating | work | selfcare | spending | trend | lifestyle",
  "template_type": "webtoon_6",
  "cuts": [
    {{"type": "dialogue", "speaker": "other", "text": "문자열"}},
    {{"type": "dialogue", "speaker": "me", "text": "문자열"}},
    {{"type": "dialogue", "speaker": "me | other | fox", "text": "문자열"}},
    {{"type": "dialogue", "speaker": "me | other | fox", "text": "문자열"}},
    {{"type": "narration | dialogue", "speaker": "none | me | other | fox", "text": "문자열"}},
    {{"type": "fact | dialogue", "speaker": "fox", "text": "문자열"}}
  ],
  "caption": "문자열",
  "hashtags": ["#태그1", "#태그2", "#태그3"],
  "visuals": {{
    "background": "파일명.png",
    "cut1": "파일명.png",
    "cut2": "파일명.png",
    "cut3": "파일명.png",
    "cut4": "파일명.png",
    "cut5": "파일명.png",
    "cut6": "파일명.png"
  }}
}}
""".strip()


def validate_generated_content(
    payload: dict[str, Any],
    expected_topic: FilteredTopic,
) -> GeneratedContent:
    required_keys = {
    "title",
    "topic",
    "category",
    "template_type",
        "cuts",
        "caption",
        "hashtags",
        "visuals",
    }
    missing = required_keys - payload.keys()
    if missing:
        raise ValueError(f"응답 필드 누락: {sorted(missing)}")

    category = str(payload["category"]).strip()
    if category not in {"selfcare", "work", "dating", "spending", "trend", "lifestyle"}:
        raise ValueError(f"허용되지 않은 category: {category}")
    if category != expected_topic.category:
        raise ValueError(
            f"요청 category 와 응답 category 불일치: {expected_topic.category} != {category}"
        )

    template_type = str(payload["template_type"]).strip()
    if template_type != "webtoon_6":
        raise ValueError("template_type 은 webtoon_6 이어야 합니다.")

    hashtags_raw = payload["hashtags"]
    if not isinstance(hashtags_raw, list) or not hashtags_raw:
        raise ValueError("hashtags 는 비어 있지 않은 배열이어야 합니다.")

    visuals_raw = payload["visuals"]
    if not isinstance(visuals_raw, dict):
        raise ValueError("visuals 는 객체여야 합니다.")

    hashtags = [_normalize_hashtag(str(item)) for item in hashtags_raw if str(item).strip()]
    if len(hashtags) < 3:
        raise ValueError("hashtags 는 최소 3개가 필요합니다.")

    cuts_raw = payload["cuts"]
    if not isinstance(cuts_raw, list) or len(cuts_raw) != 6:
        raise ValueError("cuts 는 6개 객체 리스트여야 합니다.")

    cuts: list[CutLine] = []
    for item in cuts_raw:
        if not isinstance(item, dict):
            raise ValueError("cuts 각 항목은 객체여야 합니다.")
        cut_type = str(item.get("type", "")).strip()
        speaker = str(item.get("speaker", "")).strip()
        text = _clean_text(str(item.get("text", "")))
        if cut_type not in {"dialogue", "narration", "fact"}:
            raise ValueError(f"허용되지 않은 cut type: {cut_type}")
        if speaker not in {"fox", "me", "other", "none"}:
            raise ValueError(f"허용되지 않은 speaker: {speaker}")
        if not text:
            raise ValueError("컷 텍스트가 비어 있습니다.")
        cuts.append(CutLine(type=cut_type, speaker=speaker, text=text))

    content = GeneratedContent(
        title=_clean_text(str(payload["title"])),
        topic=expected_topic.topic,
        category=category,
        template_type=template_type,
        cuts=cuts,
        caption=_clean_text(str(payload["caption"])),
        hashtags=hashtags[:3],
        visuals=VisualSelection(
            background=_clean_text(str(visuals_raw.get("background", ""))),
            cut1=_clean_text(str(visuals_raw.get("cut1", ""))),
            cut2=_clean_text(str(visuals_raw.get("cut2", ""))),
            cut3=_clean_text(str(visuals_raw.get("cut3", ""))),
            cut4=_clean_text(str(visuals_raw.get("cut4", ""))),
            cut5=_clean_text(str(visuals_raw.get("cut5", ""))),
            cut6=_clean_text(str(visuals_raw.get("cut6", ""))),
        ),
    )

    for field_name in ("title", "caption"):
        if not getattr(content, field_name):
            raise ValueError(f"{field_name} 이 비어 있습니다.")
    _validate_copy_quality(content)
    return content


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_hashtag(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return cleaned


def _validate_copy_quality(content: GeneratedContent) -> None:
    banned_terms = {
        "증상",
        "진단",
        "치료",
        "질환",
        "유산",
        "탈구",
        "설명",
        "정의",
        "뜻",
        "영어로",
        "우리 모두",
        "힘내",
        "속상",
        "어쩌면",
    }
    text_blob = " ".join(
        [
            content.title,
            *[cut.text for cut in content.cuts],
            content.caption,
            content.topic,
        ]
    )
    if any(term in text_blob for term in banned_terms):
        raise ValueError("사전식/의료식/위로형 표현이 포함되어 있습니다.")

    if len(content.title.replace(" ", "")) > 18:
        raise ValueError("title 이 너무 깁니다.")

    if content.cuts[5].speaker != "fox":
        raise ValueError("마지막 컷은 fox 화자여야 합니다.")

    if content.cuts[5].type not in {"fact", "dialogue"}:
        raise ValueError("마지막 컷은 fact 또는 dialogue 타입이어야 합니다.")

    if len(content.cut6.replace(" ", "")) < 5:
        raise ValueError("cut6 가 너무 짧아 결론이 약합니다.")
