from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config import Settings
from content_generator import GeneratedContent
from topic_filter import Category
from pollinations_generator import generate_background


VISUAL_RULES: dict[Category, dict[str, str]] = {
    "dating": {
        "background": "chat.png",
        "cut1": "phone_looking.png",
        "cut2": "judging.png",
        "cut3": "neutral_front.png",
        "cut4": "annoyed.png",
        "cut5": "sitting_blank.png",
        "cut6": "closeup_face.png",
    },
    "work": {
        "background": "office.png",
        "cut1": "arms_crossed.png",
        "cut2": "pointing.png",
        "cut3": "judging.png",
        "cut4": "annoyed.png",
        "cut5": "sitting_blank.png",
        "cut6": "closeup_face.png",
    },
    "selfcare": {
        "background": "home.png",
        "cut1": "lying_down.png",
        "cut2": "sitting_blank.png",
        "cut3": "neutral_front.png",
        "cut4": "annoyed.png",
        "cut5": "lying_down.png",
        "cut6": "closeup_face.png",
    },
    "spending": {
        "background": "shopping.png",
        "cut1": "phone_looking.png",
        "cut2": "judging.png",
        "cut3": "neutral_front.png",
        "cut4": "judging.png",
        "cut5": "sitting_blank.png",
        "cut6": "pointing.png",
    },
    "trend": {
        "background": "blank.png",
        "cut1": "neutral_front.png",
        "cut2": "judging.png",
        "cut3": "annoyed.png",
        "cut4": "sitting_blank.png",
        "cut5": "judging.png",
        "cut6": "closeup_face.png",
    },
    "lifestyle": {
        "background": "home.png",
        "cut1": "neutral_front.png",
        "cut2": "sitting_blank.png",
        "cut3": "judging.png",
        "cut4": "annoyed.png",
        "cut5": "sitting_blank.png",
        "cut6": "closeup_face.png",
    },
}


@dataclass(frozen=True)
class ResolvedVisuals:
    background: Path | None
    cuts: list[Path]


def resolve_visuals(
    content: GeneratedContent,
    settings: Settings,
    logger: logging.Logger,
) -> ResolvedVisuals | None:
    fallback = VISUAL_RULES[content.category]
    background = _resolve_background(
        requested_name=content.visuals.background,
        fallback_name=fallback["background"],
        settings=settings,
        logger=logger,
        category=content.category,
    )

    cut_paths: list[Path] = []
    for index in range(1, 7):
        cut_paths.append(
            _resolve_fox_asset(
                getattr(content.visuals, f"cut{index}"),
                fallback[f"cut{index}"],
                settings,
                logger,
            )
        )

    if any(path is None for path in cut_paths):
        logger.error("필수 에셋 누락으로 렌더링 불가 | title=%s", content.title)
        return None

    return ResolvedVisuals(background=background, cuts=[path for path in cut_paths if path is not None])


def _resolve_background(
    requested_name: str,
    fallback_name: str,
    settings: Settings,
    logger: logging.Logger,
    category: str = "default",
) -> Path | None:
    for filename in (requested_name, fallback_name):
        if not filename:
            continue
        path = settings.background_assets_dir / filename
        if path.exists():
            return path
        logger.warning("배경 파일 없음 | %s", path)

    # 정적 에셋 없으면 Pollinations.ai로 자동 생성
    generated_path = settings.background_assets_dir / f"generated_{category}.png"
    return generate_background(category=category, save_path=generated_path)


def _resolve_fox_asset(
    requested_name: str,
    fallback_name: str,
    settings: Settings,
    logger: logging.Logger,
) -> Path | None:
    for filename in (requested_name, fallback_name):
        if not filename:
            continue
        path = settings.fox_assets_dir / filename
        if path.exists():
            return path
        logger.warning("여우 에셋 파일 없음 | %s", path)
    return None
