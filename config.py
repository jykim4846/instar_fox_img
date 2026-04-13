from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


class ConfigError(ValueError):
    """필수 환경변수가 비어 있을 때 사용한다."""


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
    )
