from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date as date_cls, timedelta
from pathlib import Path


DEFAULT_HISTORY_PATH = Path("output") / "recent_topics.json"


@dataclass(frozen=True)
class TopicHistoryEntry:
    date: str
    category: str
    canonical: str


def load_history(path: Path = DEFAULT_HISTORY_PATH) -> list[TopicHistoryEntry]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    entries = payload.get("history", [])
    return [
        TopicHistoryEntry(
            date=item["date"],
            category=item.get("category", ""),
            canonical=item.get("canonical", ""),
        )
        for item in entries
        if isinstance(item, dict) and "date" in item
    ]


def append_history(
    canonical: str,
    category: str,
    *,
    today: str | None = None,
    path: Path = DEFAULT_HISTORY_PATH,
    keep_days: int = 30,
) -> None:
    today = today or date_cls.today().isoformat()
    history = [entry for entry in load_history(path) if entry.date != today]
    history.append(TopicHistoryEntry(date=today, category=category, canonical=canonical))
    cutoff = (date_cls.today() - timedelta(days=keep_days)).isoformat()
    history = [entry for entry in history if entry.date >= cutoff]
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "history": [
            {"date": e.date, "category": e.category, "canonical": e.canonical}
            for e in history
        ]
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_canonicals(
    history: list[TopicHistoryEntry], *, days: int, today: str | None = None
) -> set[str]:
    today_d = date_cls.fromisoformat(today) if today else date_cls.today()
    cutoff = (today_d - timedelta(days=days)).isoformat()
    return {entry.canonical for entry in history if entry.date >= cutoff and entry.canonical}


def recent_categories(
    history: list[TopicHistoryEntry], *, days: int, today: str | None = None
) -> set[str]:
    today_d = date_cls.fromisoformat(today) if today else date_cls.today()
    cutoff = (today_d - timedelta(days=days)).isoformat()
    return {entry.category for entry in history if entry.date >= cutoff and entry.category}
