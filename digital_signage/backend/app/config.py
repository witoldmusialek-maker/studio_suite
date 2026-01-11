"""
Konfiguracja aplikacji
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Ustawienia aplikacji"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/digital_signage"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Application
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Content Storage
    CONTENT_DIR: str = "./content"
    CONTENT_ORIGINAL_DIR: str = "./content/original"
    CONTENT_PROCESSED_DIR: str = "./content/processed"
    CONTENT_THUMBNAILS_DIR: str = "./content/thumbnails"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Google Drive (opcjonalnie)
    GOOGLE_DRIVE_CLIENT_ID: Optional[str] = None
    GOOGLE_DRIVE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_DRIVE_REDIRECT_URI: Optional[str] = None
    
    # Bells
    BELLS_SOUNDS_DIR: str = "./content/sounds"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

