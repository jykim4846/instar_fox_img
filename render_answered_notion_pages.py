from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from notion_client import Client

from config import ConfigError, load_settings
from logger import setup_logger
from manual_worry_solution import ManualWorrySolution
from worry_solution_renderer import WorrySolutionRenderer


@dataclass(frozen=True)
class AnsweredPage:
    page_id: str
    title: str
    worry: str
    category: str
    source: str
    worry_summary: str
    writer_answer: str
    workflow_stage: str


def run(limit: int = 10) -> int:
    try:
        settings = load_settings()
    except ConfigError as error:
        print(f"[ERROR] 설정 로드 실패: {error}")
        return 1

    logger = setup_logger(settings.log_file)
    notion = Client(auth=settings.notion_api_key)
    data_source_id = _resolve_data_source_id(notion, settings.notion_database_id)
    if data_source_id is None:
        logger.error("Notion data source 를 찾지 못했습니다.")
        return 1

    pages = _fetch_answered_pages(notion, data_source_id, limit)
    if not pages:
        logger.info("WriterAnswer 가 있는 Collected/Answered 페이지가 없습니다.")
        return 0

    renderer = WorrySolutionRenderer(settings=settings, logger=logger)
    rendered_count = 0
    for page in pages:
        try:
            if page.workflow_stage == "Collected":
                notion.pages.update(
                    page_id=page.page_id,
                    properties={"WorkflowStage": {"select": {"name": "Answered"}}},
                )
                logger.info("WorkflowStage 변경 | Collected -> Answered | %s", page.title)
            manual = _to_manual_solution(page)
            result = renderer.render(manual)
            if result is None:
                continue
            _append_rendered_images(notion, page.page_id, result.worry_path, result.solution_path)
            notion.pages.update(
                page_id=page.page_id,
                properties={"WorkflowStage": {"select": {"name": "Rendered"}}},
            )
            rendered_count += 1
            logger.info("Notion 답변 렌더 성공 | %s", page.title)
        except Exception as error:  # noqa: BLE001
            logger.error("Notion 답변 렌더 실패 | %s | %s", page.title, error)

    logger.info("Answered 페이지 렌더 종료 | %s건", rendered_count)
    return 0 if rendered_count > 0 else 1


def _resolve_data_source_id(notion: Client, database_id: str) -> str | None:
    database = notion.databases.retrieve(database_id=database_id)
    data_sources = database.get("data_sources", [])
    if not data_sources:
        return None
    return data_sources[0].get("id")


def _fetch_answered_pages(notion: Client, data_source_id: str, limit: int) -> list[AnsweredPage]:
    pages: list[AnsweredPage] = []
    cursor: str | None = None

    while len(pages) < limit:
        response = notion.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=cursor,
            page_size=min(100, limit),
        )
        for page in response.get("results", []):
            properties = page.get("properties", {})
            workflow_stage = _read_select(properties.get("WorkflowStage", {}))
            writer_answer = _read_rich_text(properties.get("WriterAnswer", {}))
            if workflow_stage not in {"Collected", "Answered"} or not writer_answer.strip():
                continue
            pages.append(
                AnsweredPage(
                    page_id=page["id"],
                    title=_read_title(properties.get("Title", {})) or _read_rich_text(properties.get("Worry", {})),
                    worry=_read_rich_text(properties.get("Worry", {})),
                    category=_read_select(properties.get("Category", {})) or "lifestyle",
                    source=_read_rich_text(properties.get("Source", {})),
                    worry_summary=_read_rich_text(properties.get("WorrySummary", {})),
                    writer_answer=writer_answer,
                    workflow_stage=workflow_stage,
                )
            )
            if len(pages) >= limit:
                break

        if len(pages) >= limit or not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def _to_manual_solution(page: AnsweredPage) -> ManualWorrySolution:
    answer_lines = [line.strip() for line in page.writer_answer.splitlines() if line.strip()]
    if len(answer_lines) < 3:
        raise ValueError("WriterAnswer 는 최소 3줄 필요합니다. 첫 줄 제목, 마지막 줄 결론.")

    solution_title = answer_lines[0]
    final_line = answer_lines[-1]
    solution_body = answer_lines[1:-1]
    worry_story = _build_worry_story(page)

    return ManualWorrySolution(
        title=page.title,
        category=page.category,
        worry=page.worry,
        source=page.source,
        worry_summary=page.worry or page.worry_summary or page.title,
        worry_story=worry_story,
        solution_title=solution_title,
        solution_body=solution_body,
        final_line=final_line,
        fox_pose=_default_fox_pose(page.category),
        background=_default_background(page.category),
    )


def _build_worry_story(page: AnsweredPage) -> list[str]:
    story = _split_story_sentences(page.worry_summary)
    if len(story) >= 2:
        return story[:4]
    if page.worry_summary:
        return [page.worry_summary, page.worry or page.title]
    return [page.worry or page.title, page.source or "고민 수집 결과"]


def _split_story_sentences(text: str) -> list[str]:
    normalized = " ".join(text.replace("\n", " ").split())
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?다요])\s+", normalized)
    cleaned = [part.strip() for part in parts if part.strip()]
    if len(cleaned) >= 2:
        return cleaned
    fallback = [part.strip() for part in normalized.split(".") if part.strip()]
    return fallback


def _append_rendered_images(notion: Client, page_id: str, worry_path: Path, solution_path: Path) -> None:
    worry_upload_id = _create_file_upload(notion, worry_path)
    solution_upload_id = _create_file_upload(notion, solution_path)
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            _heading_block("Rendered Cards"),
            _paragraph_block("Worry Slide"),
            _image_block(worry_upload_id),
            _paragraph_block("Solution Slide"),
            _image_block(solution_upload_id),
        ],
    )


def _create_file_upload(notion: Client, path: Path) -> str:
    upload = notion.file_uploads.create(
        mode="single_part",
        filename=path.name,
        content_type="image/png",
    )
    file_upload_id = upload["id"]
    with path.open("rb") as image_file:
        notion.file_uploads.send(
            file_upload_id=file_upload_id,
            file=(path.name, image_file, "image/png"),
        )
    return file_upload_id


def _image_block(file_upload_id: str) -> dict:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
        },
    }


def _heading_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _read_title(property_value: dict) -> str:
    title = property_value.get("title", [])
    return "".join(item.get("plain_text", "") for item in title).strip()


def _read_rich_text(property_value: dict) -> str:
    rich_text = property_value.get("rich_text", [])
    return "".join(item.get("plain_text", "") for item in rich_text).strip()


def _read_select(property_value: dict) -> str:
    select_value = property_value.get("select")
    if isinstance(select_value, dict):
        return str(select_value.get("name", "")).strip()
    return ""


def _default_background(category: str) -> str:
    backgrounds = {
        "dating": "chat.png",
        "work": "office.png",
        "selfcare": "home.png",
        "spending": "shopping.png",
        "trend": "blank.png",
        "lifestyle": "home.png",
    }
    return backgrounds.get(category, "blank.png")


def _default_fox_pose(category: str) -> str:
    poses = {
        "dating": "judging.png",
        "work": "arms_crossed.png",
        "selfcare": "sitting_blank.png",
        "spending": "pointing.png",
        "trend": "closeup_face.png",
        "lifestyle": "judging.png",
    }
    return poses.get(category, "judging.png")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    raise SystemExit(run(limit))
