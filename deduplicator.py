from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from notion_client import Client

from config import Settings
from topic_filter import FilteredTopic


@dataclass(frozen=True)
class RecentTopic:
    title: str
    topic: str


class Deduplicator:
    def __init__(
        self,
        notion: Client,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.notion = notion
        self.settings = settings
        self.logger = logger

    def filter_recent_duplicates(
        self,
        topics: list[FilteredTopic],
    ) -> list[FilteredTopic]:
        recent_topics = self.fetch_recent_topics()
        if not recent_topics:
            return topics

        unique_topics: list[FilteredTopic] = []
        for candidate in topics:
            if self._is_duplicate(candidate, recent_topics):
                self.logger.info("중복 주제 제외 | topic=%s", candidate.topic)
                continue
            unique_topics.append(candidate)
        return unique_topics

    def fetch_recent_topics(self) -> list[RecentTopic]:
        cutoff_date = (
            datetime.now(self.settings.zoneinfo) - timedelta(days=self.settings.dedupe_window_days)
        ).date()
        results: list[RecentTopic] = []
        cursor: str | None = None

        while True:
            try:
                response = self.notion.databases.query(
                    database_id=self.settings.notion_database_id,
                    filter={
                        "property": "CreatedAt",
                        "date": {"on_or_after": cutoff_date.isoformat()},
                    },
                    start_cursor=cursor,
                    page_size=100,
                )
            except Exception as error:  # noqa: BLE001
                self.logger.warning("최근 Notion 항목 조회 실패: %s", error)
                return []

            for page in response.get("results", []):
                properties = page.get("properties", {})
                results.append(
                    RecentTopic(
                        title=_read_title(properties.get("Title", {})),
                        topic=_read_rich_text(properties.get("Topic", {})),
                    )
                )

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        self.logger.info("최근 Notion 항목 조회 완료 | %s개", len(results))
        return results

    def _is_duplicate(
        self,
        candidate: FilteredTopic,
        recent_topics: list[RecentTopic],
    ) -> bool:
        candidate_values = [candidate.keyword, candidate.topic]

        for recent in recent_topics:
            recent_values = [recent.title, recent.topic]
            for left in candidate_values:
                for right in recent_values:
                    if _is_similar(left, right):
                        return True
        return False


def _read_title(property_value: dict) -> str:
    title = property_value.get("title", [])
    return "".join(item.get("plain_text", "") for item in title).strip()


def _read_rich_text(property_value: dict) -> str:
    rich_text = property_value.get("rich_text", [])
    return "".join(item.get("plain_text", "") for item in rich_text).strip()


def _is_similar(left: str, right: str) -> bool:
    left_norm = _normalize(left)
    right_norm = _normalize(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    if left_norm in right_norm or right_norm in left_norm:
        return min(len(left_norm), len(right_norm)) >= 6

    left_tokens = set(_tokenize(left))
    right_tokens = set(_tokenize(right))
    if left_tokens and right_tokens:
        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        if overlap >= 0.5:
            return True

    ratio = SequenceMatcher(None, left_norm, right_norm).ratio()
    return ratio >= 0.82


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[0-9a-z가-힣]+", value.lower())


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", value.lower())
