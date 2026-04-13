from __future__ import annotations

import logging
from dataclasses import dataclass

from notion_client import Client

from config import Settings
from daily_worry import RankedWorry


@dataclass(frozen=True)
class CollectedWorryRecord:
    title: str
    worry: str
    category: str
    source: str
    worry_summary: str
    collection_reason: str
    created_at: str
    post_date: str


class NotionWriter:
    def __init__(self, notion: Client, settings: Settings, logger: logging.Logger) -> None:
        self.notion = notion
        self.settings = settings
        self.logger = logger

    def write_collected_worry(self, record: CollectedWorryRecord) -> bool:
        property_map = {
            "Title": {"title": [_text_block(record.title)]},
            "Worry": {"rich_text": [_text_block(record.worry)]},
            "Category": {"select": {"name": record.category}},
            "Source": {"rich_text": [_text_block(record.source)]},
            "WorrySummary": {"rich_text": [_text_block(record.worry_summary)]},
            "Status": {"status": {"name": "Draft"}},
            "WorkflowStage": {"select": {"name": "Collected"}},
            "CreatedAt": {"date": {"start": record.created_at}},
            "PostDate": {"date": {"start": record.post_date}},
        }

        try:
            page = self.notion.pages.create(
                parent={"database_id": self.settings.notion_database_id},
                properties=property_map,
            )
            page_id = page["id"]
            self.notion.blocks.children.append(
                block_id=page_id,
                children=[
                    _heading_block("Collected Worry"),
                    _paragraph_block(record.worry),
                    _heading_block("Worry Story"),
                    _paragraph_block(record.worry_summary),
                    _heading_block("Collection Reason"),
                    _paragraph_block(record.collection_reason),
                    _heading_block("How To Use"),
                    _paragraph_block("WriterAnswer 에 여러 줄로 답변을 적는다. 첫 줄은 제목, 마지막 줄은 결론으로 사용된다."),
                ],
            )
            self.logger.info("Notion 고민 저장 성공 | %s", record.title)
            return True
        except Exception as error:  # noqa: BLE001
            missing_props = _extract_missing_properties(str(error))
            if missing_props:
                self.logger.warning("누락된 Notion 속성은 건너뜁니다 | %s", ", ".join(missing_props))
                try:
                    filtered = {
                        key: value for key, value in property_map.items() if key not in missing_props
                    }
                    self.notion.pages.create(
                        parent={"database_id": self.settings.notion_database_id},
                        properties=filtered,
                    )
                    self.logger.info(
                        "Notion 고민 저장 성공(부분 속성) | %s | missing=%s",
                        record.title,
                        ", ".join(missing_props),
                    )
                    return True
                except Exception as retry_error:  # noqa: BLE001
                    self.logger.error("Notion 고민 저장 재시도 실패 | %s | %s", record.title, retry_error)
            self.logger.error("Notion 고민 저장 실패 | %s | %s", record.title, error)
            return False


def to_collected_worry_record(
    worry: RankedWorry,
    *,
    category: str,
    source: str,
    created_at: str,
    post_date: str,
) -> CollectedWorryRecord:
    return CollectedWorryRecord(
        title=worry.normalized_worry[:80],
        worry=worry.normalized_worry,
        category=category,
        source=source,
        worry_summary=" ".join(worry.story),
        collection_reason=worry.reason,
        created_at=created_at,
        post_date=post_date,
    )


def _text_block(value: str) -> dict:
    return {"type": "text", "text": {"content": value[:2000]}}


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


def _extract_missing_properties(error_message: str) -> list[str]:
    properties: list[str] = []
    for chunk in error_message.split("."):
        chunk = chunk.strip()
        if "is not a property that exists" not in chunk:
            continue
        property_name = chunk.replace("is not a property that exists", "").strip()
        if property_name:
            properties.append(property_name)
    return properties
