from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from daily_estj_reel_writer import build_estj_reel_card
from daily_trend_ranker import RankedTrend, collect_ranked_trends, save_ranking
from estj_content import ESTJCard
from estj_reel_renderer import render_estj_reel
from logger import setup_logger

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
# 니치 (<1만) — 경쟁 적어 상위 노출 용이
_TAGS_NICHE_ESTJ = [
    "#ESTJ특징", "#ESTJ일상", "#ESTJ여우", "#여우리",
    "#MBTI캐릭터", "#계획형인간", "#ESTJ공감", "#ESTJ밈",
    "#여우리ESTJ", "#MBTI일상", "#ESTJ짤", "#ESTJ카드",
    "#ESTJ유형", "#MBTI짤", "#ESTJ공감짤", "#MBTI카드",
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

    post_to_ig = bool(os.getenv("IG_USER_ID") and os.getenv("META_ACCESS_TOKEN"))

    # ── ESTJ 릴스 ────────────────────────────────
    logger.info("트렌드 기반 ESTJ 콘텐츠 생성 시작")
    ranked = collect_ranked_trends(logger=logger)
    winner = ranked[0] if ranked else None
    if ranked:
        save_ranking(ranked, output_dir)
        logger.info("ESTJ 릴스 주제 선정 | %s | score=%s", winner.keyword, winner.final_score)
    estj_card, estj_reel_path = render_daily_estj_reel(winner, ranked, output_dir, logger)
    print(f"[ESTJ릴스] {estj_reel_path}")
    print(f"           제목: {estj_card.title}")

    # ── 인스타그램 게시 (ESTJ 릴스만) ─────────────
    estj_hashtags = _build_estj_hashtags(estj_card.hashtags)

    if post_to_ig:
        from instagram_poster import InstagramPoster

        poster = InstagramPoster(logger=logger)
        estj_reel_caption = f"{estj_card.title} 🦊\n\n{estj_hashtags}"
        poster.post_reel(estj_reel_path, caption=estj_reel_caption)
    else:
        logger.info("IG 환경변수 없음 - 인스타 게시 스킵 (로컬 테스트 모드)")

    return 0


def render_daily_estj_reel(
    winner: RankedTrend | None,
    ranked: list[RankedTrend],
    output_dir: Path,
    logger,
) -> tuple[ESTJCard, Path]:
    estj_card = build_estj_reel_card(winner, ranked, logger)
    estj_reel_path = output_dir / "estj_reel.mp4"
    render_estj_reel(estj_card, estj_reel_path)
    logger.info("ESTJ 릴스 생성 완료 | %s | %s", estj_card.title, estj_reel_path)
    return estj_card, estj_reel_path


if __name__ == "__main__":
    sys.exit(run())
