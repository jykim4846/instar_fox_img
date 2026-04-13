from __future__ import annotations

import logging
from pathlib import Path

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
        property_map = {
            "Title": {"title": [_text_block(candidate.title)]},
            "Topic": {"rich_text": [_text_block(candidate.topic)]},
            "Category": {"select": {"name": candidate.category}},
            "TemplateType": {"select": {"name": candidate.template_type}},
            "Cut1": {"rich_text": [_text_block(candidate.cut1)]},
            "Cut2": {"rich_text": [_text_block(candidate.cut2)]},
            "Cut3": {"rich_text": [_text_block(candidate.cut3)]},
            "Caption": {"rich_text": [_text_block(candidate.caption)]},
            "Hashtags": {"rich_text": [_text_block(hashtags)]},
            "Status": {"status": {"name": "Draft"}},
            "AIScore": {"number": candidate.ai_score},
            "Recommended": {"checkbox": candidate.recommended},
            "PreviewImage1": {"rich_text": [_text_block(candidate.preview_image1)]},
            "PreviewImage2": {"rich_text": [_text_block(candidate.preview_image2)]},
            "PreviewImage3": {"rich_text": [_text_block(candidate.preview_image3)]},
            "Source": {"rich_text": [_text_block(candidate.source)]},
            "CreatedAt": {"date": {"start": candidate.created_at}},
            "PostDate": {"date": {"start": candidate.post_date}},
        }

        try:
            page = self.notion.pages.create(
                parent={"database_id": self.settings.notion_database_id},
                properties=property_map,
            )
            page_id = page["id"]
            try:
                uploaded_urls = self._attach_rendered_images(page_id, candidate)
                if uploaded_urls:
                    self.notion.pages.update(
                        page_id=page_id,
                        properties={
                            "PreviewImage1": {"rich_text": [_text_block(uploaded_urls[0])]},
                            "PreviewImage2": {"rich_text": [_text_block(uploaded_urls[1])]},
                            "PreviewImage3": {"rich_text": [_text_block(uploaded_urls[2])]},
                        },
                    )
            except Exception as error:  # noqa: BLE001
                self.logger.error("Notion 이미지 첨부 실패 | title=%s | %s", candidate.title, error)
            self.logger.info(
                "Notion 저장 성공 | title=%s | score=%s | recommended=%s",
                candidate.title,
                candidate.ai_score,
                candidate.recommended,
            )
            return True
        except Exception as error:  # noqa: BLE001
            missing_props = _extract_missing_properties(str(error))
            if missing_props:
                self.logger.warning("누락된 Notion 속성은 건너뜁니다 | %s", ", ".join(missing_props))
                try:
                    filtered = {
                        key: value for key, value in property_map.items() if key not in missing_props
                    }
                    page = self.notion.pages.create(
                        parent={"database_id": self.settings.notion_database_id},
                        properties=filtered,
                    )
                    page_id = page["id"]
                    try:
                        uploaded_urls = self._attach_rendered_images(page_id, candidate)
                        if uploaded_urls:
                            updates = {}
                            if "PreviewImage1" not in missing_props:
                                updates["PreviewImage1"] = {"rich_text": [_text_block(uploaded_urls[0])]}
                            if "PreviewImage2" not in missing_props:
                                updates["PreviewImage2"] = {"rich_text": [_text_block(uploaded_urls[1])]}
                            if "PreviewImage3" not in missing_props:
                                updates["PreviewImage3"] = {"rich_text": [_text_block(uploaded_urls[2])]}
                            if updates:
                                self.notion.pages.update(page_id=page_id, properties=updates)
                    except Exception as image_error:  # noqa: BLE001
                        self.logger.error(
                            "Notion 이미지 첨부 실패 | title=%s | %s",
                            candidate.title,
                            image_error,
                        )
                    self.logger.info(
                        "Notion 저장 성공(부분 속성) | title=%s | 누락 속성=%s",
                        candidate.title,
                        ", ".join(missing_props),
                    )
                    return True
                except Exception as retry_error:  # noqa: BLE001
                    self.logger.error(
                        "Notion 재시도 저장 실패 | title=%s | %s",
                        candidate.title,
                        retry_error,
                    )
            self.logger.error("Notion 저장 실패 | title=%s | %s", candidate.title, error)
            return False

    def _attach_rendered_images(
        self,
        page_id: str,
        candidate: RankedCandidate,
    ) -> list[str]:
        paths = [
            candidate.preview_image1_path,
            candidate.preview_image2_path,
            candidate.preview_image3_path,
        ]

        if not all(paths):
            return []

        uploaded_urls: list[str] = []
        heading_added = False

        for index, path in enumerate(paths, start=1):
            if path is None or not path.exists():
                self.logger.warning("미리보기 이미지 파일 없음 | %s", path)
                return []

            file_upload = self.notion.file_uploads.create(
                mode="single_part",
                filename=path.name,
                content_type="image/png",
            )
            file_upload_id = file_upload["id"]
            with path.open("rb") as image_file:
                self.notion.file_uploads.send(
                    file_upload_id=file_upload_id,
                    file=(path.name, image_file, "image/png"),
                )

            children = []
            if not heading_added:
                children.append(
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Rendered Slides"}}]
                        },
                    }
                )
                heading_added = True

            children.append(
                _caption_block(f"Slide {index}")
            )
            children.append(
                {
                    "object": "block",
                    "type": "image",
                    "image": {
                        "caption": [],
                        "type": "file_upload",
                        "file_upload": {"id": file_upload_id},
                    },
                }
            )
            response = self.notion.blocks.children.append(block_id=page_id, children=children)
            uploaded_url = _extract_latest_image_url(response)
            uploaded_urls.append(uploaded_url or str(path))
        return uploaded_urls


def _extract_latest_image_url(response: dict) -> str | None:
    for block in reversed(response.get("results", [])):
        if block.get("type") != "image":
            continue
        image = block.get("image", {})
        if image.get("type") == "file":
            return image.get("file", {}).get("url")
    return None


def _caption_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _text_block(value: str) -> dict:
    return {
        "type": "text",
        "text": {"content": value[:2000]},
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
