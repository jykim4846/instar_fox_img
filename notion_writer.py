from __future__ import annotations

import logging

from notion_client import Client

from config import Settings
from scorer import RankedCandidate


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

    def write_draft(self, candidate: RankedCandidate) -> bool:
        hashtags = " ".join(candidate.hashtags)
        try:
            self.notion.pages.create(
                parent={"database_id": self.settings.notion_database_id},
                properties={
                    "Title": {"title": [_text_block(candidate.title)]},
                    "Topic": {"rich_text": [_text_block(candidate.topic)]},
                    "Category": {"select": {"name": candidate.category}},
                    "Cut1": {"rich_text": [_text_block(candidate.cut1)]},
                    "Cut2": {"rich_text": [_text_block(candidate.cut2)]},
                    "Cut3": {"rich_text": [_text_block(candidate.cut3)]},
                    "Caption": {"rich_text": [_text_block(candidate.caption)]},
                    "Hashtags": {"rich_text": [_text_block(hashtags)]},
                    "AIScore": {"number": candidate.ai_score},
                    "Recommended": {"checkbox": candidate.recommended},
                    "Status": {"status": {"name": "Draft"}},
                    "PreviewText": {"rich_text": [_text_block(candidate.preview_text)]},
                    "PostDate": {"date": {"start": candidate.post_date}},
                },
            )
            self.logger.info(
                "Notion 저장 성공 | title=%s | score=%s | recommended=%s",
                candidate.title,
                candidate.ai_score,
                candidate.recommended,
            )
            return True
        except Exception as error:  # noqa: BLE001
            self.logger.error("Notion 저장 실패 | title=%s | %s", candidate.title, error)
            return False


def _text_block(value: str) -> dict:
    return {
        "type": "text",
        "text": {"content": value[:2000]},
    }
