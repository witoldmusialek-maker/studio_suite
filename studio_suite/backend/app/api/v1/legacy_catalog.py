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
    LegacyCatalogResponse,
    UpdateBundleItemPriceRequest,
    UpdateBundlePriceRequest,
    UpdateServicePriceRequest,
)
from app.services.legacy_catalog_service import (
    add_bundle_item,
    create_bundle,
    delete_bundle,
    delete_bundle_item,
    get_legacy_catalog,
    update_bundle_item_price,
    update_bundle_price,
    update_service_price,
)

router = APIRouter(prefix="/legacy/catalog", tags=["legacy-catalog"])


@router.get("", response_model=LegacyCatalogResponse)
async def get_catalog(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return get_legacy_catalog(db)


@router.patch("/services/{service_id}/price")
async def patch_service_price(
    service_id: int,
    payload: UpdateServicePriceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    try:
        return update_service_price(db, service_id=service_id, salon_id=1, price=payload.price)
    except ValueError as err:
        if str(err) == "service_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bundle code already exists")
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
