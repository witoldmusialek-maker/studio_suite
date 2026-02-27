"""
API v1 - rejestracja routerów
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    legacy_reports,
    legacy_catalog,
    resources,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(legacy_reports.router)
api_router.include_router(legacy_catalog.router)
api_router.include_router(resources.router)
