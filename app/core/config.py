import uuid
from typing import Annotated

from pydantic import EmailStr, field_validator, model_validator
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

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    magic_link_expire_minutes: int = 15

    # Kill switch: when False, all requests are treated as auth_bypass_user_id.
    auth_enabled: bool = True
    auth_bypass_user_id: uuid.UUID | None = None

    resend_api_key: str = ""
    resend_timeout_seconds: int = 5
    email_from: EmailStr = "noreply@example.com"
    frontend_url: str = "http://localhost:3000"

    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 1000
    llm_timeout_s: float = 30
    openai_api_key: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Allow CORS_ORIGINS to be a comma-separated string in the env file."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def _require_bypass_user_when_auth_disabled(self) -> "Settings":
        """Fail fast rather than silently letting every request through as no one."""
        if not self.auth_enabled and self.auth_bypass_user_id is None:
            raise ValueError("AUTH_BYPASS_USER_ID is required when AUTH_ENABLED is False")
        return self


settings = Settings()
