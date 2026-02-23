"""
Główny plik aplikacji FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import api_router
from app.database import Base, engine
from app import models  # noqa: F401 - ensure model metadata is registered

APP_VERSION = "v1.0.0-beta.2026-02-19.9"

# Utworzenie aplikacji
app = FastAPI(
    title="Digital Signage API",
    description="API dla systemu zarządzania treścią wyświetlaczy",
    version=APP_VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def startup() -> None:
    """Initialize database schema for local/dev environments."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Endpoint główny"""
    return {
        "message": "Digital Signage API",
        "version": APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": APP_VERSION}
