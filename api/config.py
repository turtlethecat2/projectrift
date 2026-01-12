"""
Configuration management for Project Rift API
Loads and validates environment variables using Pydantic
"""

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database Configuration
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "project_rift"
    DB_USER: str
    DB_PASSWORD: str

    # API Security
    WEBHOOK_SECRET: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Application Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SOUND_VOLUME: float = 0.7

    # HUD Settings
    HUD_REFRESH_INTERVAL: int = 5
    HUD_OPACITY: float = 0.85

    # dbt Settings
    DBT_PROFILES_DIR: str = "./dbt_project"
    DBT_TARGET: str = "dev"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Optional External Services
    OUTREACH_API_KEY: Optional[str] = None
    NOOKS_API_KEY: Optional[str] = None

    @validator('WEBHOOK_SECRET')
    def validate_secret_length(cls, v):
        """Ensure webhook secret is at least 32 characters"""
        if len(v) < 32:
            raise ValueError('WEBHOOK_SECRET must be at least 32 characters for security')
        return v

    @validator('SOUND_VOLUME', 'HUD_OPACITY')
    def validate_percentage(cls, v):
        """Ensure values are between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Value must be between 0.0 and 1.0')
        return v

    @validator('HUD_REFRESH_INTERVAL')
    def validate_refresh_interval(cls, v):
        """Ensure refresh interval is at least 1 second"""
        if v < 1:
            raise ValueError('HUD_REFRESH_INTERVAL must be at least 1 second')
        return v

    @validator('RATE_LIMIT_PER_MINUTE')
    def validate_rate_limit(cls, v):
        """Ensure rate limit is positive"""
        if v <= 0:
            raise ValueError('RATE_LIMIT_PER_MINUTE must be positive')
        return v

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
