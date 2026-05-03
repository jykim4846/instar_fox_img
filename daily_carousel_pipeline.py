from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from carousel_ai_trend_renderer import render_slides
from daily_carousel_writer import build_carousel_content, save_content
from daily_trend_ranker import collect_ranked_trends, save_ranking
from logger import setup_logger


REQUIRED_POST_ENV = (
    "IG_USER_ID",
    "META_ACCESS_TOKEN",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


def run(*, dry_run: bool = False) -> int:
    load_dotenv()
    today = datetime.now().date().isoformat()
    output_dir = Path("output") / "daily_carousel" / today
    logger = setup_logger(Path("logs") / "daily_carousel_pipeline.log")

    ranked = collect_ranked_trends(logger=logger)
    if not ranked:
        logger.error("게시 가능한 트렌드 후보가 없습니다.")
        return 1

    save_ranking(ranked, output_dir)
    winner = ranked[0]
    logger.info("오늘의 캐러셀 주제 선정 | %s | score=%s", winner.keyword, winner.final_score)

    content = build_carousel_content(winner)
    save_content(content, output_dir)
    image_paths = render_slides(content.slides, output_dir)
    logger.info("캐러셀 렌더 완료 | %s장 | %s", len(image_paths), output_dir)

    if dry_run:
        print(output_dir)
        for image_path in image_paths:
            print(image_path)
        print(content.caption)
        return 0

    missing = [key for key in REQUIRED_POST_ENV if not os.getenv(key, "").strip()]
    if missing:
        logger.error("필수 게시 환경변수 누락 | %s", ", ".join(missing))
        return 2

    from instagram_poster import InstagramPoster

    poster = InstagramPoster(logger=logger)
    return 0 if poster.post_carousel(image_paths, content.caption) else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank today's trend and post one carousel.")
    parser.add_argument("--dry-run", action="store_true", help="Render and save outputs without posting.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run(dry_run=args.dry_run))
