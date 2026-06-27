"""Application settings loaded from environment variables or a local ``.env`` file."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the test framework.

    Values come from environment variables first, then from ``.env``.
    ``github_token`` stays optional on purpose: a subset of the suite must run
    unauthenticated to exercise the anonymous rate-limit tier.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    base_url: str = Field(default="https://api.github.com", validation_alias="GITHUB_API_BASE_URL")
    github_token: str | None = Field(default=None, validation_alias="GITHUB_TOKEN")
    request_timeout: float = Field(default=10.0, validation_alias="REQUEST_TIMEOUT")


def get_settings() -> Settings:
    """Build a fresh Settings instance (no caching: tests may patch the environment)."""
    return Settings()
