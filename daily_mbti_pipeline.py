from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from carousel_ai_trend_renderer import render_slides
from logger import setup_logger
from mbti_ranking_writer import (
    build_mbti_ranking,
    save_content,
    select_topic,
)
from topic_history import (
    append_history,
    load_history,
    recent_canonicals,
)


REQUIRED_POST_ENV = (
    "IG_USER_ID",
    "META_ACCESS_TOKEN",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


MBTI_COOLDOWN_DAYS = 56  # 8 weeks


def run(*, dry_run: bool = False) -> int:
    load_dotenv()
    logger = setup_logger(Path("logs") / "daily_mbti_pipeline.log")
    today = date.today().isoformat()
    output_dir = Path("output") / today / "mbti_ranking"
    output_dir.mkdir(parents=True, exist_ok=True)

    history = load_history()
    recent = recent_canonicals(history, days=MBTI_COOLDOWN_DAYS, today=today)
    topic = select_topic(recent)
    logger.info("MBTI 랭킹 토픽 선정 | %s | cooldown 적용 %s개", topic, len(recent))

    content = build_mbti_ranking(topic, logger)
    save_content(content, output_dir)
    image_paths = render_slides(content.slides, output_dir)
    logger.info("MBTI 랭킹 캐러셀 렌더 완료 | %s장 | %s", len(image_paths), output_dir)

    if dry_run:
        print(f"topic={topic}")
        for path in image_paths:
            print(path)
        print("---caption---")
        print(content.caption)
        return 0

    missing = [key for key in REQUIRED_POST_ENV if not os.getenv(key, "").strip()]
    if missing:
        logger.error("필수 게시 환경변수 누락 | %s", ", ".join(missing))
        return 2

    from instagram_poster import InstagramPoster

    poster = InstagramPoster(logger=logger)
    ok = poster.post_carousel(image_paths, content.caption)
    if ok:
        append_history(canonical=topic, category="mbti_ranking", today=today)
    return 0 if ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MBTI ranking carousel pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Render without posting.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run(dry_run=args.dry_run))
