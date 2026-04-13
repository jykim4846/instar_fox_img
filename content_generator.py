from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI

from config import Settings
from topic_filter import FilteredTopic


Category = Literal["selfcare", "work", "dating", "spending", "trend", "lifestyle"]

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
            "cut1": {"type": "string"},
            "cut2": {"type": "string"},
            "cut3": {"type": "string"},
            "caption": {"type": "string"},
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "title",
            "topic",
            "category",
            "cut1",
            "cut2",
            "cut3",
            "caption",
            "hashtags",
        ],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class GeneratedContent:
    title: str
    topic: str
    category: Category
    cut1: str
    cut2: str
    cut3: str
    caption: str
    hashtags: list[str]


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
                    max_output_tokens=500,
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
너는 인스타 캐릭터 계정 estj_fox의 콘텐츠 작가다.
캐릭터는 귀여운 사막여우지만 말투는 ESTJ처럼 현실적이고 단정적이다.
공감은 하되 감정 과장은 하지 않는다.
짧고 저장하고 싶은 문장을 만든다.
모든 출력은 한국어여야 한다.
JSON 외 텍스트를 절대 출력하지 않는다.
과장, 오글거림, 장문, 설명체, 감정 과잉은 금지다.
정치, 사건사고, 범죄, 성적 주제, 혐오, 민감 이슈는 다루지 마라.
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
  "category": "selfcare | work | dating | spending | trend | lifestyle",
  "cut1": "문자열",
  "cut2": "문자열",
  "cut3": "문자열",
  "caption": "문자열",
  "hashtags": ["#태그1", "#태그2", "#태그3"]
}}

규칙:
- JSON만 출력
- topic 값은 "{topic.topic}" 유지
- category 값은 "{topic.category}" 유지
- cut1 은 훅
- cut2 는 상황 설명
- cut3 는 여우리의 팩트 결론
- 각 cut 은 가능하면 18자 내외
- 각 cut 은 1~2문장 이내
- 마지막 cut 은 반드시 단정적인 결론
- 짧고 현실적인 말투
- 설명하지 말고 찌르듯 말하기
- 위로형, 블로그체, 교훈체, 과한 유행어 금지
- 해시태그는 3개만
- 과도하게 공격적인 표현 금지
""".strip()


def validate_generated_content(
    payload: dict[str, Any],
    expected_topic: FilteredTopic,
) -> GeneratedContent:
    required_keys = {
        "title",
        "topic",
        "category",
        "cut1",
        "cut2",
        "cut3",
        "caption",
        "hashtags",
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

    hashtags_raw = payload["hashtags"]
    if not isinstance(hashtags_raw, list) or not hashtags_raw:
        raise ValueError("hashtags 는 비어 있지 않은 배열이어야 합니다.")

    hashtags = [_normalize_hashtag(str(item)) for item in hashtags_raw if str(item).strip()]
    if len(hashtags) < 3:
        raise ValueError("hashtags 는 최소 3개가 필요합니다.")

    content = GeneratedContent(
        title=_clean_text(str(payload["title"])),
        topic=expected_topic.topic,
        category=category,
        cut1=_clean_text(str(payload["cut1"])),
        cut2=_clean_text(str(payload["cut2"])),
        cut3=_clean_text(str(payload["cut3"])),
        caption=_clean_text(str(payload["caption"])),
        hashtags=hashtags[:3],
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
