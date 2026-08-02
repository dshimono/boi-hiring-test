from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/db"
    # Time to establish a new pooled connection.
    db_connect_timeout_seconds: int = 5
    # Recycle pooled connections before an intermediary's idle limit closes them silently.
    db_pool_recycle_seconds: int = 1800
    # Server-side kill switch for a runaway query, independent of the client giving up.
    db_statement_timeout_ms: int = 10_000

    static_dir: str = "static/ads"

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Allow CORS_ORIGINS to be a comma-separated string in the env file."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Build the Settings singleton once and cache it for the process lifetime."""
    return Settings()


settings = get_settings()
