from __future__ import annotations

import logging

from notion_client import Client

from canva_generator import CanvaDesign
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

    def write_draft(
        self,
        candidate: RankedCandidate,
        canva_designs: list[CanvaDesign] | None = None,
    ) -> bool:
        hashtags = " ".join(candidate.hashtags)
        payload = {
            "parent": {"database_id": self.settings.notion_database_id},
            "properties": {
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
        }
        children = _build_children(canva_designs or [])
        if children:
            payload["children"] = children

        try:
            self.notion.pages.create(**payload)
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


def _build_children(canva_designs: list[CanvaDesign]) -> list[dict]:
    if not canva_designs:
        return []

    children: list[dict] = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Canva Designs"},
                    }
                ]
            },
        }
    ]

    for design in canva_designs:
        edit_rich_text = (
            {
                "type": "text",
                "text": {
                    "content": "Edit",
                    "link": {"url": design.edit_url},
                },
            }
            if design.edit_url
            else {
                "type": "text",
                "text": {"content": "Edit URL 없음"},
            }
        )
        view_rich_text = (
            {
                "type": "text",
                "text": {
                    "content": "View",
                    "link": {"url": design.view_url},
                },
            }
            if design.view_url
            else {
                "type": "text",
                "text": {"content": "View URL 없음"},
            }
        )
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{design.template_name}: "},
                        },
                        edit_rich_text,
                        {
                            "type": "text",
                            "text": {"content": " | "},
                        },
                        view_rich_text,
                    ]
                },
            }
        )

    return children
