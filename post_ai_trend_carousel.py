from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from carousel_ai_trend_renderer import render_carousel
from instagram_poster import InstagramPoster
from logger import setup_logger


CAPTION = """AI를 쓰는 사람이 특별한 게 아니라
이제는 안 쓰는 사람이 설명해야 하는 분위기가 됐다.

하지만 중요한 건 "AI를 쓰냐 안 쓰냐"가 아니라
AI에게 어디까지 맡기고, 어디부터 내가 판단하느냐다.

속도는 도구가 만들 수 있지만
기준은 아직 사람이 만들어야 한다.

당신은 AI에게 어디까지 맡기나요?
초안 / 요약 / 아이디어 / 판단 중 하나만 고른다면?

#AI트렌드 #생성형AI #업무효율 #콘텐츠기획 #카드뉴스 #일하는방식 #생산성"""


REQUIRED_ENV = (
    "IG_USER_ID",
    "META_ACCESS_TOKEN",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


def run() -> int:
    load_dotenv()
    logger = setup_logger(Path("logs") / "ai_trend_carousel.log")

    missing = [key for key in REQUIRED_ENV if not os.getenv(key, "").strip()]
    if missing:
        logger.error("필수 환경변수 누락 | %s", ", ".join(missing))
        return 2

    image_paths = render_carousel()
    logger.info("캐러셀 이미지 렌더 완료 | %s장", len(image_paths))

    poster = InstagramPoster(logger=logger)
    return 0 if poster.post_carousel(image_paths, CAPTION) else 1


if __name__ == "__main__":
    sys.exit(run())
