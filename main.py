from __future__ import annotations

import sys

from notion_client import Client

from config import ConfigError, load_settings
from content_generator import ContentGenerator
from deduplicator import Deduplicator
from logger import setup_logger
from notion_writer import NotionWriter
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
        logger.warning("필터링 후 남은 주제가 없습니다.")
        return 0

    notion = Client(auth=settings.notion_api_key)
    deduplicator = Deduplicator(notion=notion, settings=settings, logger=logger)
    unique_topics = deduplicator.filter_recent_duplicates(filtered_topics)
    if not unique_topics:
        logger.warning("중복 제거 후 남은 주제가 없습니다.")
        return 0

    generator = ContentGenerator(settings=settings, logger=logger)
    writer = NotionWriter(notion=notion, settings=settings, logger=logger)

    saved_count = 0
    for topic in unique_topics[: settings.max_topics_per_run]:
        generated = generator.generate(topic)
        if generated is None:
            continue

        source = f"{topic.source} | keyword={topic.keyword}"
        saved = writer.write_draft(generated, source=source)
        if saved:
            saved_count += 1

    logger.info("파이프라인 종료 | 저장 성공 %s건", saved_count)

    # TODO: Canva 템플릿 연결
    # TODO: Approved 상태 전환 후 Instagram 자동 업로드
    # TODO: 주제 랭킹 점수화
    return 0 if saved_count > 0 else 1


if __name__ == "__main__":
    sys.exit(run())
