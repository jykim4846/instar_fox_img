from __future__ import annotations

import sys
from datetime import datetime

from notion_client import Client

from config import ConfigError, load_settings
from daily_worry import DailyWorryCollector
from logger import setup_logger
from notion_writer import NotionWriter, to_collected_worry_record


def run() -> int:
    try:
        settings = load_settings()
    except ConfigError as error:
        print(f"[ERROR] 설정 로드 실패: {error}")
        return 1

    logger = setup_logger(settings.log_file)
    logger.info("고민 수집 파이프라인 시작")

    collector = DailyWorryCollector(logger=logger)
    worries = collector.collect()
    if not worries:
        logger.warning("수집된 고민이 없습니다.")
        return 1

    notion = Client(auth=settings.notion_api_key)
    writer = NotionWriter(notion=notion, settings=settings, logger=logger)

    created_at = datetime.now(settings.zoneinfo).isoformat()
    post_date = datetime.now(settings.zoneinfo).date().isoformat()
    saved_count = 0

    for worry in worries:
        record = to_collected_worry_record(
            worry,
            category=_infer_category(worry.normalized_worry),
            source=" / ".join(worry.matched_signals[:3]) or "daily_worry",
            created_at=created_at,
            post_date=post_date,
        )
        if writer.write_collected_worry(record):
            saved_count += 1

    logger.info("고민 수집 파이프라인 종료 | 저장 성공 %s건", saved_count)
    return 0 if saved_count > 0 else 1


def _infer_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("답장", "읽씹", "연애", "썸", "만나")):
        return "dating"
    if any(token in lowered for token in ("회사", "퇴사", "이직", "직장", "업무")):
        return "work"
    if any(token in lowered for token in ("소비", "쇼핑", "절약", "돈", "가계부")):
        return "spending"
    if any(token in lowered for token in ("루틴", "운동", "습관", "자기관리")):
        return "selfcare"
    if any(token in lowered for token in ("친구", "관계", "거리")):
        return "lifestyle"
    return "trend"


if __name__ == "__main__":
    sys.exit(run())
