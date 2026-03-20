from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.api.v1 import public_auth, public_booking

APP_VERSION = "v1.0.0-beta.2026-03-14.T30"

app = FastAPI(
    title="Studio Suite Public API",
    description="Publiczne API rezerwacji online",
    version=APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_booking.router, prefix=settings.API_V1_PREFIX)
app.include_router(public_auth.router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def set_security_headers(request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}
