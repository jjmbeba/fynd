from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["production", "development", "test"] = "development"
    database_url: AnyUrl
    cors_origins: list[str] = []

    api_prefix: str = "/api"

    fx_base_currency: str = "KES"
    fx_provider_url: str = "https://api.frankfurter.app"

    scrape_hour_local: int = 6

    log_level: str = "INFO"

    sentry_dsn: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
