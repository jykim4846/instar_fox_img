from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManualWorrySolution:
    title: str
    category: str
    worry: str
    source: str
    worry_summary: str
    worry_story: list[str]
    solution_title: str
    solution_body: list[str]
    final_line: str
    fox_pose: str
    background: str


def load_manual_worry_solution(json_path: Path) -> ManualWorrySolution:
    with json_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    required = {
        "title",
        "category",
        "worry",
        "source",
        "worry_summary",
        "worry_story",
        "solution_title",
        "solution_body",
        "final_line",
        "fox_pose",
        "background",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"필수 필드 누락: {sorted(missing)}")

    worry_story = [_clean_text(str(item)) for item in payload["worry_story"]]
    solution_body = [_clean_text(str(item)) for item in payload["solution_body"]]
    if len(worry_story) < 2:
        raise ValueError("worry_story 는 최소 2줄 필요합니다.")
    if len(solution_body) < 2:
        raise ValueError("solution_body 는 최소 2줄 필요합니다.")

    return ManualWorrySolution(
        title=_clean_text(str(payload["title"])),
        category=_clean_text(str(payload["category"])),
        worry=_clean_text(str(payload["worry"])),
        source=_clean_text(str(payload["source"])),
        worry_summary=_clean_text(str(payload["worry_summary"])),
        worry_story=worry_story,
        solution_title=_clean_text(str(payload["solution_title"])),
        solution_body=solution_body,
        final_line=_clean_text(str(payload["final_line"])),
        fox_pose=_clean_text(str(payload["fox_pose"])),
        background=_clean_text(str(payload["background"])),
    )


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())
