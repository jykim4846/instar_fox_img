from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from daily_carousel_pipeline import render_daily_carousel
from daily_trend_ranker import collect_ranked_trends, save_ranking
from logger import setup_logger
from pipeline import _build_estj_hashtags, render_daily_estj_reel


REQUIRED_POST_ENV = (
    "IG_USER_ID",
    "META_ACCESS_TOKEN",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


def run(*, dry_run: bool = False) -> int:
    load_dotenv()
    logger = setup_logger(Path("logs") / "daily_content_pipeline.log")
    today = str(date.today())
    output_dir = Path("output") / today
    carousel_dir = output_dir / "carousel"
    output_dir.mkdir(parents=True, exist_ok=True)

    ranked = collect_ranked_trends(logger=logger)
    if not ranked:
        logger.error("게시 가능한 트렌드 후보가 없습니다.")
        return 1

    save_ranking(ranked, output_dir)
    winner = ranked[0]
    logger.info("오늘의 공통 주제 선정 | %s | score=%s", winner.keyword, winner.final_score)

    estj_card, estj_reel_path = render_daily_estj_reel(winner, ranked, output_dir, logger)
    carousel_content, carousel_paths = render_daily_carousel(winner, ranked, carousel_dir, logger)

    if dry_run:
        print(f"topic={winner.keyword} score={winner.final_score}")
        print(estj_reel_path)
        for image_path in carousel_paths:
            print(image_path)
        print(carousel_content.caption)
        return 0

    missing = [key for key in REQUIRED_POST_ENV if not os.getenv(key, "").strip()]
    if missing:
        logger.error("필수 게시 환경변수 누락 | %s", ", ".join(missing))
        return 2

    from instagram_poster import InstagramPoster

    poster = InstagramPoster(logger=logger)
    estj_caption = f"{estj_card.title}\n\n{_build_estj_hashtags(estj_card.hashtags)}"
    estj_ok = poster.post_reel(estj_reel_path, estj_caption)
    carousel_ok = poster.post_carousel(carousel_paths, carousel_content.caption)
    return 0 if estj_ok and carousel_ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank one topic and publish ESTJ reel plus carousel.")
    parser.add_argument("--dry-run", action="store_true", help="Render outputs without posting.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run(dry_run=args.dry_run))
