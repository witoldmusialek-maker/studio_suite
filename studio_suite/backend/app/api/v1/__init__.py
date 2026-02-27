"""
API v1 - rejestracja routerów
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    booking,
    inventory,
    legacy_reports,
    legacy_catalog,
    recipe,
    reports,
    resources,
    sales,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(booking.router)
api_router.include_router(inventory.router)
api_router.include_router(legacy_reports.router)
api_router.include_router(legacy_catalog.router)
api_router.include_router(recipe.router)
api_router.include_router(reports.router)
api_router.include_router(resources.router)
api_router.include_router(sales.router)
