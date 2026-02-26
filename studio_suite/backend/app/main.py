"""
GÄąâ€šÄ‚Ĺ‚wny plik aplikacji FastAPI
"""
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.api.v1 import api_router
from app.database import Base, engine
from app import models  # noqa: F401 - ensure model metadata is registered

APP_VERSION = "v1.0.0-beta.2026-02-26.07"

# Utworzenie aplikacji
app = FastAPI(
    title="Studio Suite API",
    description="API dla systemu zarzĂ„â€¦dzania treÄąâ€şciĂ„â€¦ wyÄąâ€şwietlaczy",
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

# Rejestracja routerÄ‚Ĺ‚w
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def set_security_headers(request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.on_event("startup")
def startup() -> None:
    """Initialize database schema for local/dev environments."""
    if engine.dialect.name == "postgresql":
        # Keep enum in sync on existing deployments without explicit Alembic migrations.
        with engine.begin() as conn:
            enum_exists = conn.execute(
                text("SELECT 1 FROM pg_type WHERE typname = 'userrole'")
            ).scalar()
            if enum_exists:
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'OPERATOR_DISPLAYS'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'OPERATOR_BELLS'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MANAGER'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'EMPLOYEE'"))
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Endpoint gÄąâ€šÄ‚Ĺ‚wny"""
    return {
        "message": "Studio Suite API",
        "version": APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": APP_VERSION}

