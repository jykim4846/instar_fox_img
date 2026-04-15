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

# ── 해시태그 풀 (대형 / 중형 / 니치 3계층) ──────────
# 대형 (100만+ 게시물) — 짧은 노출, 유입 트리거
_TAGS_LARGE = [
    "#MBTI", "#일상", "#공감", "#인스타그램", "#일상스타그램",
    "#공감스타그램", "#소통", "#daily", "#instadaily",
]
# 중형 (1만~100만) — 탐색 탭 노출 핵심
_TAGS_MEDIUM_ESTJ = [
    "#ESTJ", "#MBTI유형", "#MBTI공감", "#성격유형", "#MBTI밈",
    "#MBTI스타그램", "#성격테스트", "#MBTI결과",
]
_TAGS_MEDIUM_TREND = [
    "#트렌드", "#뉴스", "#이슈", "#오늘의뉴스", "#핫이슈",
    "#실시간뉴스", "#trending", "#korea", "#뉴스스타그램",
]
# 니치 (<1만) — 경쟁 적어 상위 노출 용이
_TAGS_NICHE_ESTJ = [
    "#ESTJ특징", "#ESTJ일상", "#ESTJ여우", "#여우리",
    "#MBTI캐릭터", "#계획형인간", "#ESTJ공감", "#ESTJ밈",
    "#여우리ESTJ", "#MBTI일상",
]
_TAGS_NICHE_TREND = [
    "#여우리", "#오늘의트렌드", "#여우리트렌드",
    "#MBTI캐릭터", "#뉴스정리", "#트렌드정리",
]

MAX_TAGS = 25


def _merge_tags(*pools: list[str], limit: int = MAX_TAGS) -> list[str]:
    """여러 태그 풀을 중복 없이 순서대로 합친다."""
    seen: set[str] = set()
    result: list[str] = []
    for pool in pools:
        for tag in pool:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                result.append(tag)
            if len(result) >= limit:
                return result
    return result


def _build_trend_hashtags(items) -> str:
    keyword_tags = []
    for item in items:
        for word in item.keyword.split():
            tag = word.strip("[]()「」『』【】《》〈〉·…-—,.:!?\"'")
            if len(tag) >= 2 and tag not in keyword_tags:
                keyword_tags.append(tag)
    keyword_pool = [f"#{t}" for t in keyword_tags[:10]]
    tags = _merge_tags(
        _TAGS_NICHE_TREND, keyword_pool, _TAGS_MEDIUM_TREND, _TAGS_LARGE,
    )
    return " ".join(tags)


def _build_estj_hashtags(card_hashtags: str) -> str:
    card_tags = [t.strip() for t in card_hashtags.split() if t.startswith("#")]
    tags = _merge_tags(
        card_tags, _TAGS_NICHE_ESTJ, _TAGS_MEDIUM_ESTJ, _TAGS_LARGE,
    )
    return " ".join(tags)

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
    collection = collector.collect(limit=5)

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
            trend_caption = f"오늘의 트렌드 📰\n\n{_build_trend_hashtags(collection.items)}"
            poster.post(trend_path, caption=trend_caption)

        import time; time.sleep(30)  # 두 게시 사이 간격 (Meta 권장)

        estj_hashtags = _build_estj_hashtags(estj_card.hashtags)
        estj_caption = f"{estj_card.title}\n\n" + "\n".join(f"• {b}" for b in estj_card.bullets) + f"\n\n{estj_hashtags}"
        poster.post(estj_path, caption=estj_caption)
    else:
        logger.info("IG 환경변수 없음 - 인스타 게시 스킵 (로컬 테스트 모드)")

    return 0


if __name__ == "__main__":
    sys.exit(run())
