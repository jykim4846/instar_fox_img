from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from estj_content import get_today
from estj_reel_renderer import render_estj_reel
from instagram_poster import InstagramPoster
from logger import setup_logger
from trend_collector import fetch_trending_keywords
from trend_reel_renderer import render_trend_reel

# ── 해시태그 풀 (대형 / 중형 / 니치 3계층) ──────────
# 대형 (100만+ 게시물) — 짧은 노출, 유입 트리거
_TAGS_LARGE = [
    "#MBTI", "#일상", "#공감", "#인스타그램", "#일상스타그램",
    "#공감스타그램", "#소통", "#daily", "#instadaily",
    "#인스타", "#좋아요", "#팔로우", "#소통해요", "#맞팔",
]
# 중형 (1만~100만) — 탐색 탭 노출 핵심
_TAGS_MEDIUM_ESTJ = [
    "#ESTJ", "#MBTI유형", "#MBTI공감", "#성격유형", "#MBTI밈",
    "#MBTI스타그램", "#성격테스트", "#MBTI결과", "#MBTI테스트",
    "#성격분석", "#MBTI분석", "#갓생", "#자기계발", "#mbtitest",
]
_TAGS_MEDIUM_TREND = [
    "#트렌드", "#뉴스", "#이슈", "#오늘의뉴스", "#핫이슈",
    "#실시간뉴스", "#trending", "#korea", "#뉴스스타그램",
    "#시사", "#정보", "#뉴스정리", "#오늘뉴스", "#koreanews",
]
# 니치 (<1만) — 경쟁 적어 상위 노출 용이
_TAGS_NICHE_ESTJ = [
    "#ESTJ특징", "#ESTJ일상", "#ESTJ여우", "#여우리",
    "#MBTI캐릭터", "#계획형인간", "#ESTJ공감", "#ESTJ밈",
    "#여우리ESTJ", "#MBTI일상", "#ESTJ짤", "#ESTJ카드",
    "#ESTJ유형", "#MBTI짤", "#ESTJ공감짤", "#MBTI카드",
]
_TAGS_NICHE_TREND = [
    "#여우리", "#오늘의트렌드", "#여우리트렌드",
    "#MBTI캐릭터", "#트렌드정리", "#뉴스카드",
    "#오늘의이슈", "#트렌드카드", "#데일리뉴스", "#여우리뉴스",
]

MAX_TAGS = 30


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

    poster = InstagramPoster(logger=logger)
    post_to_ig = bool(os.getenv("IG_USER_ID") and os.getenv("META_ACCESS_TOKEN"))

    # ── ESTJ 릴스 ────────────────────────────────
    logger.info("ESTJ 콘텐츠 선택 시작")
    estj_card = get_today()
    estj_reel_path = output_dir / "estj_reel.mp4"
    render_estj_reel(estj_card, estj_reel_path)
    logger.info("ESTJ 릴스 생성 완료 | %s | %s", estj_card.title, estj_reel_path)
    print(f"[ESTJ릴스] {estj_reel_path}")
    print(f"           제목: {estj_card.title}")

    # ── 트렌드 릴스 ──────────────────────────────
    logger.info("트렌드 키워드 수집 시작 (Google Trends)")
    trend_keywords = fetch_trending_keywords(limit=3, logger=logger)
    trend_reel_path = None
    if len(trend_keywords) >= 3:
        trend_reel_path = output_dir / "trend_reel.mp4"
        render_trend_reel(trend_keywords, trend_reel_path)
        logger.info("트렌드 릴스 생성 완료 | %s", trend_reel_path)
        print(f"[트렌드릴스] {trend_reel_path}")
        for i, kw in enumerate(trend_keywords):
            print(f"  {i+1}위: {kw.keyword} ({kw.traffic})")
    else:
        logger.warning("트렌드 키워드 부족 (%s개) - 트렌드 릴스 스킵", len(trend_keywords))

    # ── 인스타그램 게시 (릴스만) ──────────────────
    estj_hashtags = _build_estj_hashtags(estj_card.hashtags)

    if post_to_ig:
        import time

        estj_reel_caption = f"{estj_card.title} 🦊\n\n{estj_hashtags}"
        poster.post_reel(estj_reel_path, caption=estj_reel_caption)
        time.sleep(30)

        if trend_reel_path:
            trend_reel_caption = f"오늘의 관심 키워드 TOP 3 🔥\n\n{_build_trend_hashtags(trend_keywords)}"
            poster.post_reel(trend_reel_path, caption=trend_reel_caption)
    else:
        logger.info("IG 환경변수 없음 - 인스타 게시 스킵 (로컬 테스트 모드)")

    return 0


if __name__ == "__main__":
    sys.exit(run())
