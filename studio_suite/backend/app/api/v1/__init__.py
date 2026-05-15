"""
API v1 - rejestracja routerów
"""
from fastapi import APIRouter, Depends

from app.api.deps import (
    require_active_tenant,
    require_module_booking,
    require_module_inventory,
    require_module_payments,
    require_module_reports,
    require_module_legacy_caisse,
)
from app.api.v1 import (
    auth,
    booking,
    colors,
    inventory,
    legacy_reports,
    legacy_catalog,
    legacy_caisse,
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
api_router.include_router(booking.router, dependencies=[Depends(require_module_booking)])
api_router.include_router(colors.router, dependencies=[Depends(require_module_inventory)])
api_router.include_router(inventory.router, dependencies=[Depends(require_module_inventory)])
api_router.include_router(legacy_reports.router, dependencies=[Depends(require_active_tenant)])
api_router.include_router(legacy_catalog.router, dependencies=[Depends(require_active_tenant)])
api_router.include_router(legacy_caisse.router, dependencies=[Depends(require_module_legacy_caisse)])
api_router.include_router(payments.router, dependencies=[Depends(require_module_payments)])
api_router.include_router(public_booking.router)
api_router.include_router(recipe.router, dependencies=[Depends(require_module_inventory)])
api_router.include_router(reports.router, dependencies=[Depends(require_module_reports)])
api_router.include_router(resources.router, dependencies=[Depends(require_active_tenant)])
api_router.include_router(sales.router, dependencies=[Depends(require_module_payments)])
api_router.include_router(sessions.router, dependencies=[Depends(require_active_tenant)])
api_router.include_router(tenants.router)
