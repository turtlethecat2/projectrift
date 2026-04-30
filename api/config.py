"""Load and validate environment configuration."""

from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "project_rift"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    WEBHOOK_SECRET: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SOUND_VOLUME: float = 0.7

    HUD_REFRESH_INTERVAL: int = 5
    HUD_OPACITY: float = 0.85

    DBT_PROFILES_DIR: str = "./dbt_project"
    DBT_TARGET: str = "dev"

    RATE_LIMIT_PER_MINUTE: int = 60

    OUTREACH_API_KEY: Optional[str] = None
    NOOKS_API_KEY: Optional[str] = None

    OUTREACH_CLIENT_ID: Optional[str] = None
    OUTREACH_CLIENT_SECRET: Optional[str] = None
    OUTREACH_REDIRECT_URI: Optional[str] = None
    OUTREACH_POLL_INTERVAL_MINUTES: int = 15

    @field_validator("WEBHOOK_SECRET")
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("WEBHOOK_SECRET must be at least 32 characters")
        return v

    @field_validator("SOUND_VOLUME", "HUD_OPACITY")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Value must be between 0.0 and 1.0")
        return v

    @field_validator("HUD_REFRESH_INTERVAL")
    @classmethod
    def validate_refresh_interval(cls, v: int) -> int:
        if v < 1:
            raise ValueError("HUD_REFRESH_INTERVAL must be at least 1 second")
        return v

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be positive")
        return v


settings = Settings()


def outreach_oauth_configured() -> bool:
    """True when Outreach OAuth env vars are present and not template placeholders."""
    cid = (settings.OUTREACH_CLIENT_ID or "").strip()
    csec = (settings.OUTREACH_CLIENT_SECRET or "").strip()
    uri = (settings.OUTREACH_REDIRECT_URI or "").strip()
    if not cid or not csec or not uri:
        return False
    if "your_outreach" in cid or "your_outreach" in csec:
        return False
    if "placeholder" in uri.lower():
        return False
    return True
