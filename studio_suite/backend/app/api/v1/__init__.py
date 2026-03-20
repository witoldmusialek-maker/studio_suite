"""
API v1 - rejestracja routerów
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    booking,
    colors,
    inventory,
    legacy_reports,
    legacy_catalog,
    payments,
    public_booking,
    recipe,
    reports,
    resources,
    sales,
    sessions,
    tenants,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(booking.router)
api_router.include_router(colors.router)
api_router.include_router(inventory.router)
api_router.include_router(legacy_reports.router)
api_router.include_router(legacy_catalog.router)
api_router.include_router(payments.router)
api_router.include_router(public_booking.router)
api_router.include_router(recipe.router)
api_router.include_router(reports.router)
api_router.include_router(resources.router)
api_router.include_router(sales.router)
api_router.include_router(sessions.router)
api_router.include_router(tenants.router)
