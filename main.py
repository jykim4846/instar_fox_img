from __future__ import annotations

import sys
from datetime import datetime

from notion_client import Client

from asset_mapper import resolve_visuals
from config import ConfigError, load_settings
from content_generator import ContentGenerator
from deduplicator import Deduplicator
from logger import setup_logger
from notion_writer import NotionWriter
from renderer import CarouselRenderer
from scorer import RankedCandidate, build_preview_text, score_candidate
from topic_filter import filter_topics
from trend_collector import TrendCollector


def run() -> int:
    try:
        settings = load_settings()
    except ConfigError as error:
        print(f"[ERROR] 설정 로드 실패: {error}")
        return 1

    logger = setup_logger(settings.log_file)
    logger.info("파이프라인 시작")

    trend_collector = TrendCollector(settings=settings, logger=logger)
    trend_candidates = trend_collector.collect()
    if not trend_candidates:
        logger.error("수집된 트렌드가 없어 파이프라인을 종료합니다.")
        return 1

    filtered_topics = filter_topics(
        candidates=trend_candidates,
        max_topics=settings.max_topics_per_run * 3,
        logger=logger,
    )
    if not filtered_topics:
        logger.warning(
            "필터링 후 남은 주제가 없습니다. 필터 규칙에 맞는 생활형 키워드가 부족했을 가능성이 큽니다."
        )
        return 0

    notion = Client(auth=settings.notion_api_key)
    deduplicator = Deduplicator(notion=notion, settings=settings, logger=logger)
    unique_topics = deduplicator.filter_recent_duplicates(filtered_topics)
    if not unique_topics:
        logger.warning("중복 제거 후 남은 주제가 없습니다.")
        return 0

    generator = ContentGenerator(settings=settings, logger=logger)
    renderer = CarouselRenderer(settings=settings, logger=logger)
    writer = NotionWriter(notion=notion, settings=settings, logger=logger)

    ranked_candidates: list[RankedCandidate] = []
    created_at = datetime.now(settings.zoneinfo).isoformat()
    post_date = datetime.now(settings.zoneinfo).date().isoformat()

    for topic in unique_topics:
        if len(ranked_candidates) >= settings.max_topics_per_run:
            break

        generated = generator.generate(topic)
        if generated is None:
            continue

        visuals = resolve_visuals(generated, settings=settings, logger=logger)
        if visuals is None:
            continue

        render_result = renderer.render(generated, visuals)
        if render_result is None:
            continue

        ai_score = score_candidate(generated, topic)
        ranked_candidates.append(
            RankedCandidate(
                title=generated.title,
                topic=generated.topic,
                category=generated.category,
                template_type=generated.template_type,
                cut1=generated.cut1,
                cut2=generated.cut2,
                cut3=generated.cut3,
                caption=generated.caption,
                hashtags=generated.hashtags,
                ai_score=ai_score,
                recommended=False,
                preview_text=build_preview_text(generated),
                preview_image1=render_result.slide1_ref,
                preview_image2=render_result.slide2_ref,
                preview_image3=render_result.slide3_ref,
                source=topic.source,
                created_at=created_at,
                post_date=post_date,
            )
        )
        logger.info("후보 생성 완료 | topic=%s | score=%s", topic.topic, ai_score)

    if not ranked_candidates:
        logger.warning("생성 가능한 후보가 없습니다.")
        return 0

    ranked_candidates.sort(key=lambda item: (-item.ai_score, item.title))
    ranked_candidates = [
        RankedCandidate(
            title=item.title,
            topic=item.topic,
            category=item.category,
            template_type=item.template_type,
            cut1=item.cut1,
            cut2=item.cut2,
            cut3=item.cut3,
            caption=item.caption,
            hashtags=item.hashtags,
            ai_score=item.ai_score,
            recommended=index == 0,
            preview_text=item.preview_text,
            preview_image1=item.preview_image1,
            preview_image2=item.preview_image2,
            preview_image3=item.preview_image3,
            source=item.source,
            created_at=item.created_at,
            post_date=item.post_date,
        )
        for index, item in enumerate(ranked_candidates[: settings.max_topics_per_run])
    ]

    logger.info(
        "추천순 정렬 완료 | top=%s | score=%s",
        ranked_candidates[0].title,
        ranked_candidates[0].ai_score,
    )

    saved_count = 0
    for candidate in ranked_candidates:
        if writer.write_draft(candidate):
            saved_count += 1

    logger.info("파이프라인 종료 | 저장 성공 %s건", saved_count)

    # TODO: Approved 상태와 연동한 게시 파이프라인 연결
    # TODO: 성과 데이터 기반 주제 점수 개선
    # TODO: 배경/에셋 다양화
    # TODO: 이미지 업로드 후 public URL 저장
    return 0 if saved_count > 0 else 1


if __name__ == "__main__":
    sys.exit(run())
