from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from openai import OpenAI

from config import Settings
from topic_filter import FilteredTopic


Category = Literal["selfcare", "work", "dating", "spending", "trend", "lifestyle"]


@dataclass(frozen=True)
class VisualSelection:
    background: str = ""
    cut1: str = ""
    cut2: str = ""
    cut3: str = ""


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
            "template_type": {"type": "string", "enum": ["carousel_3"]},
            "cut1": {"type": "string"},
            "cut2": {"type": "string"},
            "cut3": {"type": "string"},
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
                },
                "required": ["background", "cut1", "cut2", "cut3"],
                "additionalProperties": False,
            },
        },
        "required": [
            "title",
            "topic",
            "category",
            "template_type",
            "cut1",
            "cut2",
            "cut3",
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
    cut1: str
    cut2: str
    cut3: str
    caption: str
    hashtags: list[str]
    visuals: VisualSelection = field(default_factory=VisualSelection)


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
                    max_output_tokens=700,
                )

                raw_json = (response.output_text or "").strip()
                if not raw_json:
                    raise ValueError("OpenAI 응답이 비어 있습니다.")

                payload = json.loads(raw_json)
                content = validate_generated_content(payload, expected_topic=topic)
                self.logger.info(
                    "콘텐츠 생성 성공 | topic=%s | attempt=%s",
                    topic.topic,
                    attempt,
                )
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
항상 JSON만 출력한다.
""".strip()


def build_user_prompt(topic: FilteredTopic) -> str:
    return f"""
topic: {topic.topic}
raw_keyword: {topic.keyword}
recommended_category: {topic.category}
angle: {topic.angle}

출력 스키마:
{{
  "title": "문자열",
  "topic": "문자열",
  "category": "dating | work | selfcare | spending | trend | lifestyle",
  "template_type": "carousel_3",
  "cut1": "문자열",
  "cut2": "문자열",
  "cut3": "문자열",
  "caption": "문자열",
  "hashtags": ["#태그1", "#태그2", "#태그3"],
  "visuals": {{
    "background": "파일명.png",
    "cut1": "파일명.png",
    "cut2": "파일명.png",
    "cut3": "파일명.png"
  }}
}}

규칙:
- JSON만 출력
- 모든 텍스트는 한국어
- topic 값은 "{topic.topic}" 유지
- category 값은 "{topic.category}" 유지
- template_type 은 반드시 "carousel_3"
- cut1 은 훅
- cut2 는 상황 설명
- cut3 는 여우리의 팩트 한마디
- 한 컷은 짧아야 함
- 가능하면 18자 내외
- 문장은 짧고 단정적이어야 함
- 감정 과장 금지
- 위로형 문장 금지
- 블로그체 금지
- 설명체 금지
- 마지막 컷은 반드시 단정적인 결론
- 해시태그는 정확히 3개
- visuals 파일명은 아래 후보 중 어울리는 것을 고를 것
- 배경 후보: blank.png, office.png, home.png, bed.png, chat.png, shopping.png
- 여우 후보: neutral_front.png, annoyed.png, judging.png, arms_crossed.png, pointing.png, phone_looking.png, lying_down.png, sitting_blank.png, closeup_face.png, tiny_icon.png
- 존재하지 않을 것 같은 파일명은 만들지 말 것
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
        "cut1",
        "cut2",
        "cut3",
        "caption",
        "hashtags",
        "visuals",
    }
    missing = required_keys - payload.keys()
    if missing:
        raise ValueError(f"응답 필드 누락: {sorted(missing)}")

    category = str(payload["category"]).strip()
    if category not in {
        "selfcare",
        "work",
        "dating",
        "spending",
        "trend",
        "lifestyle",
    }:
        raise ValueError(f"허용되지 않은 category: {category}")
    if category != expected_topic.category:
        raise ValueError(
            f"요청 category 와 응답 category 불일치: {expected_topic.category} != {category}"
        )

    template_type = str(payload["template_type"]).strip()
    if template_type != "carousel_3":
        raise ValueError("template_type 은 carousel_3 이어야 합니다.")

    hashtags_raw = payload["hashtags"]
    if not isinstance(hashtags_raw, list) or not hashtags_raw:
        raise ValueError("hashtags 는 비어 있지 않은 배열이어야 합니다.")

    visuals_raw = payload["visuals"]
    if not isinstance(visuals_raw, dict):
        raise ValueError("visuals 는 객체여야 합니다.")

    hashtags = [_normalize_hashtag(str(item)) for item in hashtags_raw if str(item).strip()]
    if len(hashtags) < 3:
        raise ValueError("hashtags 는 최소 3개가 필요합니다.")

    content = GeneratedContent(
        title=_clean_text(str(payload["title"])),
        topic=expected_topic.topic,
        category=category,
        template_type=template_type,
        cut1=_clean_text(str(payload["cut1"])),
        cut2=_clean_text(str(payload["cut2"])),
        cut3=_clean_text(str(payload["cut3"])),
        caption=_clean_text(str(payload["caption"])),
        hashtags=hashtags[:3],
        visuals=VisualSelection(
            background=_clean_text(str(visuals_raw.get("background", ""))),
            cut1=_clean_text(str(visuals_raw.get("cut1", ""))),
            cut2=_clean_text(str(visuals_raw.get("cut2", ""))),
            cut3=_clean_text(str(visuals_raw.get("cut3", ""))),
        ),
    )

    for field_name in ("title", "cut1", "cut2", "cut3", "caption"):
        if not getattr(content, field_name):
            raise ValueError(f"{field_name} 이 비어 있습니다.")
    return content


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_hashtag(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return cleaned
