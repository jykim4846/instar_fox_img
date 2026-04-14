from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from estj_card_renderer import render_estj_card
from estj_content import get_today
from instagram_poster import InstagramPoster
from logger import setup_logger
from trend_card_renderer import render_trend_card
from trend_collector import TrendCollector

TREND_HASHTAGS = "#오늘의트렌드 #뉴스 #트렌드 #이슈 #여우리 #daily #trending #korea"

load_dotenv()

OUTPUT_BASE = Path("output")
LOG_FILE = Path("logs") / "pipeline.log"


def run() -> int:
    logger = setup_logger(LOG_FILE)
    today = str(date.today())
    output_dir = OUTPUT_BASE / today
    output_dir.mkdir(parents=True, exist_ok=True)

    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    if not unsplash_key:
        logger.error("UNSPLASH_ACCESS_KEY 가 설정되지 않았습니다.")
        return 1

    # ── 트렌드 카드 ──────────────────────────────
    logger.info("트렌드 수집 시작")
    collector = TrendCollector(
        unsplash_key=unsplash_key,
        logger=logger,
        output_dir=output_dir,
    )
    collection = collector.collect(limit=7)

    poster = InstagramPoster(logger=logger)
    post_to_ig = bool(os.getenv("IG_USER_ID") and os.getenv("META_ACCESS_TOKEN"))

    trend_path = None
    if collection.items:
        trend_path = output_dir / "trend_card.png"
        render_trend_card(collection, trend_path)
        logger.info("트렌드 카드 생성 완료 | %s", trend_path)
        print(f"[트렌드] {trend_path}")
    else:
        logger.warning("트렌드 아이템 없음 - 트렌드 카드 스킵")

    # ── ESTJ 카드 ────────────────────────────────
    logger.info("ESTJ 콘텐츠 선택 시작")
    estj_card = get_today()
    estj_path = output_dir / "estj_card.png"
    render_estj_card(estj_card, estj_path)
    logger.info("ESTJ 카드 생성 완료 | %s | %s", estj_card.title, estj_path)
    print(f"[ESTJ]   {estj_path}")
    print(f"         제목: {estj_card.title}")
    print(f"         태그: {estj_card.hashtags}")

    # ── 인스타그램 게시 ───────────────────────────
    if post_to_ig:
        if trend_path:
            trend_caption = f"오늘의 트렌드 📰\n\n{TREND_HASHTAGS}"
            poster.post(trend_path, caption=trend_caption)

        import time; time.sleep(30)  # 두 게시 사이 간격 (Meta 권장)

        estj_caption = f"{estj_card.title}\n\n" + "\n".join(f"• {b}" for b in estj_card.bullets) + f"\n\n{estj_card.hashtags}"
        poster.post(estj_path, caption=estj_caption)
    else:
        logger.info("IG 환경변수 없음 - 인스타 게시 스킵 (로컬 테스트 모드)")

    return 0


if __name__ == "__main__":
    sys.exit(run())
