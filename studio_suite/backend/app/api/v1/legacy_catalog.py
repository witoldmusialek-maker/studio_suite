"""
Endpoints for editable legacy catalog (prices and bundles) stored in DB.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.legacy_catalog import (
    AddBundleItemRequest,
    CreateBundleRequest,
    CreateServiceRequest,
    LegacyCatalogResponse,
    UpdateBundleItemPriceRequest,
    UpdateBundlePriceRequest,
    UpdateServicePriceRequest,
    UpdateServiceRequest,
)
from app.services.legacy_catalog_service import (
    add_bundle_item,
    create_bundle,
    create_service,
    delete_bundle,
    delete_bundle_item,
    delete_service,
    get_legacy_catalog,
    update_bundle_item_price,
    update_bundle_price,
    update_service,
    update_service_price,
)

router = APIRouter(prefix="/legacy/catalog", tags=["legacy-catalog"])


@router.get("", response_model=LegacyCatalogResponse)
async def get_catalog(
    salon_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return get_legacy_catalog(db, salon_id=salon_id)


@router.post("/services", status_code=status.HTTP_201_CREATED)
async def post_service(
    payload: CreateServiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return create_service(
            db,
            service_code=payload.service_code,
            service_name=payload.service_name,
            duration_minutes=payload.duration_minutes,
            default_price=payload.default_price,
            salon_id=payload.salon_id,
        )
    except ValueError as err:
        if str(err) == "service_code_exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service code already exists")
        if str(err) == "invalid_payload":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
        if str(err) == "salon_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        raise


@router.patch("/services/{service_id}")
async def patch_service(
    service_id: int,
    payload: UpdateServiceRequest,
    salon_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return update_service(
            db,
            service_id=service_id,
            service_name=payload.service_name,
            duration_minutes=payload.duration_minutes,
            default_price=payload.default_price,
            is_active=payload.is_active,
            local_name=payload.local_name,
            salon_id=salon_id,
        )
    except ValueError as err:
        if str(err) == "service_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        if str(err) == "invalid_payload":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
        if str(err) == "salon_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        raise


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_service(
    service_id: int,
    salon_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        delete_service(db, service_id=service_id, salon_id=salon_id)
    except ValueError as err:
        if str(err) == "service_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        if str(err) == "service_in_bundle":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete service used in bundle",
            )
        if str(err) == "salon_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        raise
    return None


@router.patch("/services/{service_id}/price")
async def patch_service_price(
    service_id: int,
    payload: UpdateServicePriceRequest,
    salon_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return update_service_price(db, service_id=service_id, salon_id=salon_id, price=payload.price)
    except ValueError as err:
        if str(err) == "service_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        if str(err) == "salon_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        raise


@router.patch("/bundles/{bundle_id}/price")
async def patch_bundle_price(
    bundle_id: int,
    payload: UpdateBundlePriceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    del payload
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Bundle price is derived from item prices. Edit item prices instead.",
    )


@router.patch("/bundles/{bundle_id}/items/{position}")
async def patch_bundle_item_price(
    bundle_id: int,
    position: int,
    payload: UpdateBundleItemPriceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return update_bundle_item_price(
            db,
            bundle_id=bundle_id,
            position=position,
            override_price=payload.override_price,
        )
    except ValueError as err:
        if str(err) == "bundle_item_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle item not found")
        raise


@router.post("/bundles")
async def post_bundle(
    payload: CreateBundleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return create_bundle(
            db,
            bundle_code=payload.bundle_code.strip(),
            bundle_name=payload.bundle_name.strip(),
            salon_id=payload.salon_id,
        )
    except ValueError as err:
        if str(err) == "bundle_code_exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bundle code already exists in salon")
        if str(err) == "salon_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        raise


@router.delete("/bundles/{bundle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bundle(
    bundle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        delete_bundle(db, bundle_id=bundle_id)
    except ValueError as err:
        if str(err) == "bundle_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        raise
    return None


@router.post("/bundles/{bundle_id}/items")
async def post_bundle_item(
    bundle_id: int,
    payload: AddBundleItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return add_bundle_item(
            db,
            bundle_id=bundle_id,
            service_id=payload.service_id,
            override_price=payload.override_price,
        )
    except ValueError as err:
        if str(err) == "bundle_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        if str(err) == "service_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        if str(err) == "service_not_available_in_salon":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service not available in bundle salon")
        raise


@router.delete("/bundles/{bundle_id}/items/{position}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bundle_item(
    bundle_id: int,
    position: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        delete_bundle_item(db, bundle_id=bundle_id, position=position)
    except ValueError as err:
        if str(err) == "bundle_item_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle item not found")
        raise
    return None
