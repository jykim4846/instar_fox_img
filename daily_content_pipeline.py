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
from topic_history import (
    append_history,
    load_history,
    recent_canonicals,
    recent_categories,
)


REQUIRED_POST_ENV = (
    "IG_USER_ID",
    "META_ACCESS_TOKEN",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


# weekday(): Mon=0 ~ Sun=6
WEEKDAY_FORMATS: dict[int, tuple[str, ...]] = {
    0: ("reel",),
    1: ("carousel",),
    2: ("reel",),
    3: ("carousel",),
    4: ("reel",),
    5: ("reel", "carousel"),
    6: ("mbti_ranking",),
}


def run(*, dry_run: bool = False) -> int:
    load_dotenv()
    logger = setup_logger(Path("logs") / "daily_content_pipeline.log")
    today_d = date.today()
    today = today_d.isoformat()
    output_dir = Path("output") / today
    carousel_dir = output_dir / "carousel"
    output_dir.mkdir(parents=True, exist_ok=True)

    formats = WEEKDAY_FORMATS.get(today_d.weekday(), ("reel",))
    if not formats:
        logger.info("오늘은 휴식일 (weekday=%s) — 게시 스킵", today_d.weekday())
        if dry_run:
            print(f"weekday={today_d.weekday()} formats=() — rest day")
        return 0
    logger.info("오늘 포맷 | weekday=%s | %s", today_d.weekday(), ",".join(formats))

    if "mbti_ranking" in formats:
        from daily_mbti_pipeline import run as run_mbti_ranking
        return run_mbti_ranking(dry_run=dry_run)

    history = load_history()
    cooldown_canonicals = recent_canonicals(history, days=3, today=today)
    cooldown_categories = recent_categories(history, days=1, today=today)
    if cooldown_canonicals or cooldown_categories:
        logger.info(
            "쿨다운 적용 | canonical(3d)=%s | category(1d)=%s",
            sorted(cooldown_canonicals),
            sorted(cooldown_categories),
        )
    ranked = collect_ranked_trends(
        logger=logger,
        recent_canonicals=cooldown_canonicals,
        recent_categories=cooldown_categories,
    )
    if not ranked:
        logger.error("게시 가능한 트렌드 후보가 없습니다.")
        return 1

    save_ranking(ranked, output_dir)
    winner = ranked[0]
    logger.info(
        "오늘의 공통 주제 선정 | %s | category=%s | score=%s",
        winner.keyword,
        winner.category,
        winner.final_score,
    )

    do_reel = "reel" in formats
    do_carousel = "carousel" in formats
    estj_card = estj_reel_path = None
    carousel_content = carousel_paths = None
    if do_reel:
        estj_card, estj_reel_path = render_daily_estj_reel(winner, ranked, output_dir, logger)
    if do_carousel:
        carousel_content, carousel_paths = render_daily_carousel(winner, ranked, carousel_dir, logger)

    if dry_run:
        print(f"topic={winner.keyword} score={winner.final_score} formats={','.join(formats)}")
        if estj_reel_path:
            print(estj_reel_path)
        if carousel_paths:
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
    estj_ok = True
    carousel_ok = True
    if do_reel:
        estj_caption = f"{estj_card.title}\n\n{_build_estj_hashtags(estj_card.hashtags)}"
        estj_ok = poster.post_reel(estj_reel_path, estj_caption)
    if do_carousel:
        carousel_ok = poster.post_carousel(carousel_paths, carousel_content.caption)
    if estj_ok or carousel_ok:
        append_history(winner.keyword, winner.category, today=today)
    return 0 if estj_ok and carousel_ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank one topic and publish ESTJ reel plus carousel.")
    parser.add_argument("--dry-run", action="store_true", help="Render outputs without posting.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run(dry_run=args.dry_run))
