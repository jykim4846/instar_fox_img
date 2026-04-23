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
class SolutionVisualSelection:
    background: str = ""
    fox_pose: str = ""


@dataclass(frozen=True)
class WorrySolutionContent:
    title: str
    topic: str
    category: Category
    template_type: str
    worry_summary: str
    worry_story: list[str]
    estj_rule: str
    solution_title: str
    solution_body: list[str]
    final_line: str
    caption: str
    hashtags: list[str]
    visuals: SolutionVisualSelection = field(default_factory=SolutionVisualSelection)


WORRY_SOLUTION_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "estj_fox_worry_solution",
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
            "template_type": {"type": "string", "enum": ["worry_solution_2"]},
            "worry_summary": {"type": "string"},
            "worry_story": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {"type": "string"},
            },
            "estj_rule": {"type": "string"},
            "solution_title": {"type": "string"},
            "solution_body": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "items": {"type": "string"},
            },
            "final_line": {"type": "string"},
            "caption": {"type": "string"},
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "visuals": {
                "type": "object",
                "properties": {
                    "background": {"type": "string"},
                    "fox_pose": {"type": "string"},
                },
                "required": ["background", "fox_pose"],
                "additionalProperties": False,
            },
        },
        "required": [
            "title",
            "topic",
            "category",
            "template_type",
            "worry_summary",
            "worry_story",
            "estj_rule",
            "solution_title",
            "solution_body",
            "final_line",
            "caption",
            "hashtags",
            "visuals",
        ],
        "additionalProperties": False,
    },
}


class WorrySolutionGenerator:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, topic: FilteredTopic) -> WorrySolutionContent | None:
        for attempt in range(1, self.settings.openai_retry_attempts + 1):
            try:
                response = self.client.responses.create(
                    model=self.settings.openai_model,
                    input=[
                        {"role": "system", "content": _build_system_prompt()},
                        {"role": "user", "content": _build_user_prompt(topic)},
                    ],
                    text={"format": WORRY_SOLUTION_SCHEMA},
                    max_output_tokens=1100,
                )
                raw_json = (response.output_text or "").strip()
                if not raw_json:
                    raise ValueError("OpenAI 응답이 비어 있습니다.")
                payload = json.loads(raw_json)
                content = _validate_content(payload, topic)
                self.logger.info("고민 솔루션 생성 성공 | topic=%s | attempt=%s", topic.topic, attempt)
                return content
            except Exception as error:  # noqa: BLE001
                self.logger.warning(
                    "고민 솔루션 생성 실패 | topic=%s | attempt=%s | %s",
                    topic.topic,
                    attempt,
                    error,
                )
        self.logger.error("고민 솔루션 최종 실패 | topic=%s", topic.topic)
        return None


def _build_system_prompt() -> str:
    return """
너는 인스타 계정 estj_fox의 전속 작가다.
형식은 2장이다.
1장은 사람들이 공감하는 고민을 서술한다.
2장은 여우리 캐릭터가 ESTJ 기준으로 솔루션을 정리한다.

여우리 판단 기준:
- 말보다 행동
- 핑계보다 패턴
- 감정보다 구조
- 미루지 말고 기준을 세운다
- 애매하면 계속 끌지 않는다

금지:
- 감정 과장
- 위로형 문장
- 블로그체
- 사전식 설명
- 정치, 범죄, 혐오, 재난, 성적 주제

출력은 반드시 JSON만 한다.
""".strip()


def _build_user_prompt(topic: FilteredTopic) -> str:
    return f"""
topic: {topic.topic}
raw_keyword: {topic.keyword}
recommended_category: {topic.category}
angle: {topic.angle}

목표:
- 1장은 고민글처럼 읽혀야 한다
- 2장은 여우리의 솔루션 카드처럼 읽혀야 한다
- 1장은 공감, 2장은 정리
- 마지막 문장은 가장 단정적이어야 한다

규칙:
- title 은 짧고 선명하게
- topic 값은 "{topic.topic}" 유지
- category 값은 "{topic.category}" 유지
- template_type 은 반드시 "worry_solution_2"
- worry_summary 는 고민의 핵심 한 줄
- worry_story 는 3~5줄, 실제 고민글처럼 자연스럽게
- estj_rule 은 여우리의 판단 기준 한 줄
- solution_title 은 카드 제목처럼 짧게
- solution_body 는 2~4줄, 행동 기준 위주
- final_line 은 저장하고 싶은 단정적인 결론
- 해시태그는 정확히 3개
- visuals.background 후보: blank.png, office.png, home.png, bed.png, chat.png, shopping.png
- visuals.fox_pose 후보: neutral_front.png, annoyed.png, judging.png, arms_crossed.png, pointing.png, phone_looking.png, lying_down.png, sitting_blank.png, closeup_face.png

출력 스키마:
{{
  "title": "문자열",
  "topic": "문자열",
  "category": "dating | work | selfcare | spending | trend | lifestyle",
  "template_type": "worry_solution_2",
  "worry_summary": "문자열",
  "worry_story": ["문자열", "문자열", "문자열"],
  "estj_rule": "문자열",
  "solution_title": "문자열",
  "solution_body": ["문자열", "문자열"],
  "final_line": "문자열",
  "caption": "문자열",
  "hashtags": ["#태그1", "#태그2", "#태그3"],
  "visuals": {{
    "background": "파일명.png",
    "fox_pose": "파일명.png"
  }}
}}
""".strip()


def _validate_content(payload: dict[str, Any], topic: FilteredTopic) -> WorrySolutionContent:
    content = WorrySolutionContent(
        title=_clean_text(str(payload["title"])),
        topic=topic.topic,
        category=str(payload["category"]).strip(),
        template_type=str(payload["template_type"]).strip(),
        worry_summary=_clean_text(str(payload["worry_summary"])),
        worry_story=[_clean_text(str(item)) for item in payload["worry_story"]],
        estj_rule=_clean_text(str(payload["estj_rule"])),
        solution_title=_clean_text(str(payload["solution_title"])),
        solution_body=[_clean_text(str(item)) for item in payload["solution_body"]],
        final_line=_clean_text(str(payload["final_line"])),
        caption=_clean_text(str(payload["caption"])),
        hashtags=[_normalize_hashtag(str(item)) for item in payload["hashtags"]],
        visuals=SolutionVisualSelection(
            background=_clean_text(str(payload["visuals"]["background"])),
            fox_pose=_clean_text(str(payload["visuals"]["fox_pose"])),
        ),
    )

    if content.category != topic.category:
        raise ValueError("category 가 요청값과 다릅니다.")
    if content.template_type != "worry_solution_2":
        raise ValueError("template_type 은 worry_solution_2 이어야 합니다.")
    if len(content.hashtags) < 3:
        raise ValueError("hashtags 는 3개 이상이어야 합니다.")
    if len(content.worry_story) < 3:
        raise ValueError("worry_story 가 너무 짧습니다.")
    if len(content.solution_body) < 2:
        raise ValueError("solution_body 가 너무 짧습니다.")
    if len(content.final_line.replace(" ", "")) < 6:
        raise ValueError("final_line 이 너무 약합니다.")
    return content


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_hashtag(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    return cleaned
