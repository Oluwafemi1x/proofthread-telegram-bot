import pytest
from pydantic import ValidationError

from proofthread.config import Settings


def settings(**overrides) -> Settings:
    values = {
        "telegram_bot_token": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk",
        "database_url": "sqlite+aiosqlite:///:memory:",
    }
    values.update(overrides)
    return Settings(**values)


def test_polling_settings_are_valid() -> None:
    config = settings()

    config.validate_mode_settings()

    assert config.mode == "polling"
    assert config.webhook_path == "/telegram/webhook"


def test_webhook_requires_url_and_secret() -> None:
    config = settings(mode="webhook")

    with pytest.raises(ValueError, match="Webhook mode requires"):
        config.validate_mode_settings()


def test_webhook_configuration_is_valid() -> None:
    config = settings(
        mode="webhook",
        webhook_base_url="https://example.com",
        webhook_secret="a-long-random-value",
    )

    config.validate_mode_settings()


def test_webhook_path_must_start_with_slash() -> None:
    with pytest.raises(ValidationError, match="must start"):
        settings(webhook_path="telegram/webhook")
