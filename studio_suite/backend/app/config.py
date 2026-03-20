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
    APP_PUBLIC_URL: str = "https://dev2.witold.ovh"
    BOOKING_BACKDATE_GRACE_MINUTES: int = 0
    DEFAULT_TENANT_CODE: str = "STUDIO_SARA"
    DEFAULT_TENANT_NAME: str = "Studio SARA sp. z o.o."
    SUPERADMIN_USERNAME: str = "superadmin"
    SUPERADMIN_PASSWORD: str = "SuperAdmin2026x"
    SUPERADMIN_TOTP_SECRET: Optional[str] = "JBSWY3DPEHPK3PXP"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # SMS / Twilio
    TWILIO_SID: Optional[str] = None
    TWILIO_TOKEN: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_FROM: Optional[str] = None
    SMS_PROVIDER: str = "TWILIO"  # TWILIO | LOCAL_HTTP
    LOCAL_SMS_URL: Optional[str] = None
    LOCAL_SMS_TOKEN: Optional[str] = None
    LOCAL_SMS_TIMEOUT_SECONDS: int = 20
    LOCAL_SMS_METHOD: str = "POST"
    PUBLIC_BOOKING_REQUIRE_OTP: bool = True
    PUBLIC_BOOKING_OTP_TTL_SECONDS: int = 300
    PUBLIC_BOOKING_OTP_MAX_ATTEMPTS: int = 5
    PUBLIC_BOOKING_RATE_LIMIT_PHONE_PER_15M: int = 5
    PUBLIC_BOOKING_RATE_LIMIT_IP_PER_15M: int = 30

    # Legacy SMB sync (Windows XP shares 05/12)
    LEGACY_SMB_HOST: str = "192.168.200.25"
    LEGACY_SMB_PORT: int = 445
    LEGACY_SMB_USE_NTLM_V2: bool = False
    LEGACY_SMB_USERNAME: str = ""
    LEGACY_SMB_PASSWORD: str = ""
    LEGACY_SMB_DOMAIN: str = ""

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
