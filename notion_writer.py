from __future__ import annotations

import logging
from datetime import datetime

from notion_client import Client

from config import Settings
from content_generator import GeneratedContent


class NotionWriter:
    def __init__(
        self,
        notion: Client,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.notion = notion
        self.settings = settings
        self.logger = logger

    def write_draft(self, content: GeneratedContent, source: str) -> bool:
        created_at = datetime.now(self.settings.zoneinfo).isoformat()
        hashtags = " ".join(content.hashtags)

        try:
            self.notion.pages.create(
                parent={"database_id": self.settings.notion_database_id},
                properties={
                    "Title": {"title": [_text_block(content.title)]},
                    "Topic": {"rich_text": [_text_block(content.topic)]},
                    "Category": {"select": {"name": content.category}},
                    "TemplateType": {"select": {"name": content.template_type}},
                    "Cut1": {"rich_text": [_text_block(content.cut1)]},
                    "Cut2": {"rich_text": [_text_block(content.cut2)]},
                    "Cut3": {"rich_text": [_text_block(content.cut3)]},
                    "Caption": {"rich_text": [_text_block(content.caption)]},
                    "Hashtags": {"rich_text": [_text_block(hashtags)]},
                    "Status": {"status": {"name": "Draft"}},
                    "CreatedAt": {"date": {"start": created_at}},
                    "Source": {"rich_text": [_text_block(source)]},
                },
            )
            self.logger.info("Notion 저장 성공 | title=%s", content.title)
            return True
        except Exception as error:  # noqa: BLE001
            self.logger.error("Notion 저장 실패 | title=%s | %s", content.title, error)
            return False


def _text_block(value: str) -> dict:
    return {
        "type": "text",
        "text": {"content": value[:2000]},
    }
