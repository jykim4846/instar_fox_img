from __future__ import annotations

from dataclasses import dataclass

from content_generator import GeneratedContent
from topic_filter import FilteredTopic


@dataclass(frozen=True)
class RankedCandidate:
    title: str
    topic: str
    category: str
    template_type: str
    cut1: str
    cut2: str
    cut3: str
    caption: str
    hashtags: list[str]
    ai_score: int
    recommended: bool
    preview_text: str
    post_date: str
    preview_image1: str = ""
    preview_image2: str = ""
    preview_image3: str = ""
    source: str = ""
    created_at: str = ""


def score_candidate(content: GeneratedContent, topic: FilteredTopic) -> int:
    score = 0
    score += _topic_priority_score(topic.priority)
    score += _category_bonus(topic.category)
    score += _source_bonus(topic.source)
    score += _keyword_clarity_bonus(topic.topic)
    score += _cuts_quality_bonus(content)
    score += _caption_bonus(content.caption)
    score += _hashtags_bonus(content.hashtags)
    return max(0, min(100, score))


def build_preview_text(content: GeneratedContent) -> str:
    preview = f"{content.cut1} | {content.cut3}"
    return preview[:120]


def _topic_priority_score(priority: int) -> int:
    return max(0, min(30, priority - 70))


def _category_bonus(category: str) -> int:
    bonuses = {
        "selfcare": 18,
        "spending": 18,
        "work": 17,
        "dating": 15,
        "trend": 14,
        "lifestyle": 13,
    }
    return bonuses.get(category, 10)


def _source_bonus(source: str) -> int:
    if "pytrends" in source.lower():
        return 10
    if "rss" in source.lower():
        return 8
    return 5


def _keyword_clarity_bonus(topic: str) -> int:
    token_count = len(topic.split())
    if token_count <= 2:
        return 12
    if token_count == 3:
        return 8
    return 4


def _cuts_quality_bonus(content: GeneratedContent) -> int:
    cuts = (content.cut1, content.cut2, content.cut3)
    bonus = 0

    for cut in cuts:
        length = len(cut.replace(" ", ""))
        if 6 <= length <= 18:
            bonus += 8
        elif length <= 24:
            bonus += 5
        else:
            bonus += 2

    if len({cut.strip() for cut in cuts}) == 3:
        bonus += 4

    if any(token in content.cut3 for token in ("답", "굳이", "낭비", "어렵지", "필요", "계속")):
        bonus += 3

    return min(30, bonus)


def _caption_bonus(caption: str) -> int:
    length = len(caption.replace(" ", ""))
    if 10 <= length <= 40:
        return 8
    if length <= 60:
        return 5
    return 2


def _hashtags_bonus(hashtags: list[str]) -> int:
    if len(hashtags) >= 3 and all(tag.startswith("#") for tag in hashtags[:3]):
        return 5
    return 0
