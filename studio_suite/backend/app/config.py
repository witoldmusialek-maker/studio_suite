"""
Konfiguracja aplikacji
"""
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ustawienia aplikacji"""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/studio_suite"

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_WINDOW_SECONDS: int = 300
    LOGIN_LOCKOUT_SECONDS: int = 900

    # Application
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    APP_TIMEZONE: str = "Europe/Warsaw"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Content Storage
    CONTENT_DIR: str = "./content"
    CONTENT_ORIGINAL_DIR: str = "./content/original"
    CONTENT_PROCESSED_DIR: str = "./content/processed"
    CONTENT_THUMBNAILS_DIR: str = "./content/thumbnails"

    # Google Drive (opcjonalnie)
    GOOGLE_DRIVE_CLIENT_ID: Optional[str] = None
    GOOGLE_DRIVE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_DRIVE_REDIRECT_URI: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if value in {"", "change-this-in-production"}:
            raise ValueError("SECRET_KEY must be set in environment")
        return value

settings = Settings()

