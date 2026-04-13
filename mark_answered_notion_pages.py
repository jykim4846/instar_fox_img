from __future__ import annotations

import sys

from notion_client import Client

from config import ConfigError, load_settings
from logger import setup_logger


def run(limit: int = 100) -> int:
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

    updated = 0
    cursor: str | None = None

    while updated < limit:
        response = notion.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=cursor,
            page_size=min(100, limit),
        )
        for page in response.get("results", []):
            properties = page.get("properties", {})
            workflow_stage = _read_select(properties.get("WorkflowStage", {}))
            writer_answer = _read_rich_text(properties.get("WriterAnswer", {}))
            if workflow_stage != "Collected":
                continue
            if not writer_answer.strip():
                continue

            notion.pages.update(
                page_id=page["id"],
                properties={"WorkflowStage": {"select": {"name": "Answered"}}},
            )
            updated += 1
            logger.info("WorkflowStage 변경 | Collected -> Answered | %s", _read_title(properties.get("Title", {})))

            if updated >= limit:
                break

        if updated >= limit or not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    logger.info("WorkflowStage 자동 전환 종료 | %s건", updated)
    return 0


def _resolve_data_source_id(notion: Client, database_id: str) -> str | None:
    database = notion.databases.retrieve(database_id=database_id)
    data_sources = database.get("data_sources", [])
    if not data_sources:
        return None
    return data_sources[0].get("id")


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


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    raise SystemExit(run(limit))
