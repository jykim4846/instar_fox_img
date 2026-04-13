from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


class ConfigError(ValueError):
    """필수 환경변수가 비어 있거나 잘못된 경우 사용한다."""


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    notion_api_key: str
    notion_database_id: str
    openai_model: str = "gpt-5.4"
    max_topics_per_run: int = 5
    locale: str = "ko-KR"
    timezone: str = "Asia/Seoul"
    min_trend_candidates: int = 10
    dedupe_window_days: int = 14
    request_timeout_seconds: int = 15
    openai_retry_attempts: int = 2
    log_dir: Path = Path("logs")
    output_dir: Path = Path("output")
    output_base_url: str = ""
    assets_dir: Path = Path("assets")
    fox_assets_dir: Path = Path("assets/fox")
    background_assets_dir: Path = Path("assets/backgrounds")
    fonts_dir: Path = Path("fonts")
    font_path: Path = Path("fonts/Pretendard-Bold.otf")
    image_size: int = 1080
    default_background_color: str = "#F7F3EA"

    @property
    def log_file(self) -> Path:
        return self.log_dir / "estj_fox_pipeline.log"

    @property
    def zoneinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def _get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise ConfigError(f"환경변수 {key} 가 필요합니다.")
    return value.strip()


def _get_int_env(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ConfigError(f"환경변수 {key} 는 정수여야 합니다.") from error


def load_settings(env_file: str | None = None) -> Settings:
    load_dotenv(dotenv_path=env_file)

    return Settings(
        openai_api_key=_get_env("OPENAI_API_KEY"),
        notion_api_key=_get_env("NOTION_API_KEY"),
        notion_database_id=_get_env("NOTION_DATABASE_ID"),
        openai_model=_get_env("OPENAI_MODEL", "gpt-5.4"),
        max_topics_per_run=_get_int_env("MAX_TOPICS_PER_RUN", 5),
        locale=_get_env("LOCALE", "ko-KR"),
        timezone=_get_env("TIMEZONE", "Asia/Seoul"),
        output_dir=Path(_get_env("OUTPUT_DIR", "./output")),
        output_base_url=os.getenv("OUTPUT_BASE_URL", "").strip(),
        assets_dir=Path(_get_env("ASSETS_DIR", "assets")),
        fox_assets_dir=Path(_get_env("FOX_ASSETS_DIR", "assets/fox")),
        background_assets_dir=Path(_get_env("BACKGROUND_ASSETS_DIR", "assets/backgrounds")),
        fonts_dir=Path(_get_env("FONTS_DIR", "fonts")),
        font_path=Path(_get_env("FONT_PATH", "fonts/Pretendard-Bold.otf")),
        image_size=_get_int_env("IMAGE_SIZE", 1080),
    )
