from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from PROOFTHREAD_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PROOFTHREAD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: SecretStr
    database_url: str = "sqlite+aiosqlite:///./data/proofthread.db"
    auto_migrate: bool = True
    mode: Literal["polling", "webhook"] = "polling"
    log_level: str = "INFO"
    default_timezone: str = "UTC"
    reminder_interval_seconds: int = Field(default=60, ge=15, le=3600)
    reminder_window_minutes: int = Field(default=15, ge=1, le=1440)

    webhook_base_url: str | None = None
    webhook_path: str = "/telegram/webhook"
    webhook_secret: SecretStr | None = None
    web_host: str = "0.0.0.0"
    web_port: int = Field(default=8080, ge=1, le=65535)

    @field_validator("webhook_path")
    @classmethod
    def validate_webhook_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("webhook_path must start with '/'")
        return value

    def validate_mode_settings(self) -> None:
        if self.mode == "webhook" and not (self.webhook_base_url and self.webhook_secret):
            raise ValueError("Webhook mode requires WEBHOOK_BASE_URL and WEBHOOK_SECRET")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    settings.validate_mode_settings()
    return settings
