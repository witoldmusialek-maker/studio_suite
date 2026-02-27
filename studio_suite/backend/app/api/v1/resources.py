"""
CRUD endpoints for salons, staff and salon product catalog.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.salon_core import (
    LegacyProductCatalogItem,
    Salon,
    StaffMember,
    StaffRole,
)
from app.models.user import User
from app.schemas.resources import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SalonCreate,
    SalonRead,
    SalonUpdate,
    StaffCreate,
    StaffFunctionRead,
    StaffRead,
    StaffUpdate,
)

router = APIRouter(prefix="/resources", tags=["resources"])


def _ensure_admin_or_manager(current_user: User) -> None:
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _staff_to_read(staff: StaffMember, salons_by_id: dict[int, Salon], roles_by_id: dict[int, StaffRole]) -> StaffRead:
    salon = salons_by_id.get(staff.salon_id) if staff.salon_id else None
    role = roles_by_id.get(staff.role_id) if staff.role_id else None
    return StaffRead(
        id=staff.id,
        display_name=staff.display_name,
        salon_id=staff.salon_id,
        salon_name=salon.name if salon else None,
        role_id=staff.role_id,
        role_name=role.name if role else None,
        is_active=bool(staff.is_active),
        legacy_code=staff.legacy_code,
    )


def _stock_100_for_salon(salon: Salon, product: LegacyProductCatalogItem) -> float | None:
    code = (salon.code or "").strip()
    name = (salon.name or "").strip().lower()
    if code == "05" or "pulaw" in name:
        return float(product.stock_mx03) if product.stock_mx03 is not None else None
    if code == "12" or "kras" in name:
        return float(product.stock_mx04) if product.stock_mx04 is not None else None
    if code == "07" or "odyn" in name:
        return float(product.stock_mx07) if product.stock_mx07 is not None else None
    return float(product.stock_mx04) if product.stock_mx04 is not None else None


def _product_to_read(product: LegacyProductCatalogItem, salon: Salon) -> ProductRead:
    return ProductRead(
        salon_product_id=product.id,
        salon_id=salon.id,
        product_id=product.id,
        product_code=product.legacy_code,
        product_name=product.name,
        product_name_pl=product.name_pl,
        fiscal_code=product.fiscal_code,
        brand=product.brand_1 or product.brand_2 or None,
        package_size_g=float(product.quantity) if product.quantity is not None else None,
        catalog_net_price=float(product.catalog_net_price) if product.catalog_net_price is not None else None,
        unit_count=float(product.unit_count) if product.unit_count is not None else None,
        warehouse=product.warehouse,
        type_code=product.type_code,
        purchase_price=float(product.purchase_price) if product.purchase_price is not None else None,
        family_code=product.family_code,
        weight=float(product.weight) if product.weight is not None else None,
        package_weight=float(product.package_weight) if product.package_weight is not None else None,
        min_unit=float(product.min_unit) if product.min_unit is not None else None,
        note=product.note,
        salon_sale_price=float(product.salon_sale_price) if product.salon_sale_price is not None else None,
        purchase_price_c=float(product.purchase_price_c) if product.purchase_price_c is not None else None,
        is_locked=bool(product.is_locked),
        sale_price_gross=float(product.sale_price_gross) if product.sale_price_gross is not None else None,
        s_u=bool(product.s_u),
        doses_short=4.0,
        doses_medium=2.0,
        doses_long=1.25,
        stock_mx03=float(product.stock_mx03) if product.stock_mx03 is not None else None,
        stock_mx04=float(product.stock_mx04) if product.stock_mx04 is not None else None,
        stock_mx07=float(product.stock_mx07) if product.stock_mx07 is not None else None,
        stock_100=_stock_100_for_salon(salon, product),
        is_active=bool(product.is_active),
    )


@router.get("/salons", response_model=list[SalonRead])
async def list_salons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(Salon).order_by(Salon.name.asc()).all()


@router.post("/salons", response_model=SalonRead, status_code=status.HTTP_201_CREATED)
async def create_salon(
    payload: SalonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    code = payload.code.strip().upper()
    name = payload.name.strip()
    if db.query(Salon).filter(Salon.code == code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Salon code already exists")
    row = Salon(code=code, name=name, is_active=payload.is_active)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/salons/{salon_id}", response_model=SalonRead)
async def update_salon(
    salon_id: int,
    payload: SalonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(Salon).filter(Salon.id == salon_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.code is not None:
        code = payload.code.strip().upper()
        existing = db.query(Salon).filter(Salon.code == code, Salon.id != salon_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Salon code already exists")
        row.code = code
    if payload.name is not None:
        row.name = payload.name.strip()
    if payload.is_active is not None:
        row.is_active = payload.is_active
    db.commit()
    db.refresh(row)
    return row


@router.delete("/salons/{salon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_salon(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(Salon).filter(Salon.id == salon_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    db.query(StaffMember).filter(StaffMember.salon_id == salon_id).update({StaffMember.salon_id: None})
    db.delete(row)
    db.commit()
    return None


@router.get("/functions", response_model=list[StaffFunctionRead])
async def list_staff_functions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(StaffRole).order_by(StaffRole.name.asc()).all()


@router.get("/staff", response_model=list[StaffRead])
async def list_staff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    staff_rows = db.query(StaffMember).order_by(StaffMember.display_name.asc()).all()
    salons = db.query(Salon).all()
    roles = db.query(StaffRole).all()
    salons_by_id = {row.id: row for row in salons}
    roles_by_id = {row.id: row for row in roles}
    return [_staff_to_read(row, salons_by_id, roles_by_id) for row in staff_rows]


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    if payload.salon_id is not None and not db.query(Salon).filter(Salon.id == payload.salon_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.role_id is not None and not db.query(StaffRole).filter(StaffRole.id == payload.role_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")

    row = StaffMember(
        display_name=payload.display_name.strip(),
        legacy_code=(payload.legacy_code or "").strip() or None,
        salon_id=payload.salon_id,
        role_id=payload.role_id,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    provided = payload.model_fields_set

    if "salon_id" in provided and payload.salon_id is not None and not db.query(Salon).filter(Salon.id == payload.salon_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if "role_id" in provided and payload.role_id is not None and not db.query(StaffRole).filter(StaffRole.id == payload.role_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")

    if "display_name" in provided and payload.display_name is not None:
        row.display_name = payload.display_name.strip()
    if "legacy_code" in provided:
        row.legacy_code = payload.legacy_code.strip() or None
    if "salon_id" in provided:
        row.salon_id = payload.salon_id
    if "role_id" in provided:
        row.role_id = payload.role_id
    if "is_active" in provided and payload.is_active is not None:
        row.is_active = payload.is_active

    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    db.delete(row)
    db.commit()
    return None


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")

    products = db.query(LegacyProductCatalogItem).order_by(LegacyProductCatalogItem.legacy_code.asc()).all()
    out: list[ProductRead] = []
    for product in products:
        out.append(_product_to_read(product, salon))
    out.sort(key=lambda item: item.product_code)
    return out


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    salons = db.query(Salon).order_by(Salon.id.asc()).all()
    if not salons:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    salon = salons[0]

    code = payload.product_code.strip().upper()
    name = payload.product_name.strip()
    if not code or not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

    product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.legacy_code == code).first()
    if product is None:
        product = LegacyProductCatalogItem(
            legacy_code=code,
            name=name,
            name_pl=(payload.product_name_pl or "").strip() or None,
            fiscal_code=(payload.fiscal_code or "").strip() or None,
            brand_1=(payload.brand or "").strip() or None,
            quantity=payload.package_size_g,
            catalog_net_price=payload.catalog_net_price,
            unit_count=payload.unit_count,
            warehouse=(payload.warehouse or "").strip() or None,
            type_code=(payload.type_code or "").strip() or None,
            purchase_price=payload.purchase_price,
            family_code=(payload.family_code or "").strip() or None,
            weight=payload.weight,
            package_weight=payload.package_weight,
            min_unit=payload.min_unit,
            note=(payload.note or "").strip() or None,
            salon_sale_price=payload.salon_sale_price,
            purchase_price_c=payload.purchase_price_c,
            is_locked=bool(payload.is_locked),
            sale_price_gross=payload.sale_price_gross,
            s_u=bool(payload.s_u),
            is_active=True,
        )
        db.add(product)
        db.flush()
    else:
        product.name = name
        product.name_pl = (payload.product_name_pl or "").strip() or None
        product.fiscal_code = (payload.fiscal_code or "").strip() or None
        if payload.brand is not None:
            product.brand_1 = (payload.brand or "").strip() or None
        product.quantity = payload.package_size_g
        product.catalog_net_price = payload.catalog_net_price
        product.unit_count = payload.unit_count
        product.warehouse = (payload.warehouse or "").strip() or None
        product.type_code = (payload.type_code or "").strip() or None
        product.purchase_price = payload.purchase_price
        product.family_code = (payload.family_code or "").strip() or None
        product.weight = payload.weight
        product.package_weight = payload.package_weight
        product.min_unit = payload.min_unit
        product.note = (payload.note or "").strip() or None
        product.salon_sale_price = payload.salon_sale_price
        product.purchase_price_c = payload.purchase_price_c
        product.is_locked = bool(payload.is_locked)
        if payload.sale_price_gross is not None:
            product.sale_price_gross = payload.sale_price_gross
        product.s_u = bool(payload.s_u)
    product.is_active = payload.is_active

    db.commit()
    db.refresh(product)
    return _product_to_read(product, salon)


@router.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    provided = payload.model_fields_set
    if product.is_locked:
        allowed_when_locked = {"is_locked"}
        if any(field not in allowed_when_locked for field in provided):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Product is locked. Unlock it first to edit other fields.",
            )
    if "product_name" in provided and payload.product_name is not None:
        clean = payload.product_name.strip()
        if clean:
            product.name = clean
    if "product_name_pl" in provided:
        product.name_pl = (payload.product_name_pl or "").strip() or None
    if "fiscal_code" in provided:
        product.fiscal_code = (payload.fiscal_code or "").strip() or None
    if "brand" in provided:
        product.brand_1 = (payload.brand or "").strip() or None
    if "package_size_g" in provided:
        product.quantity = payload.package_size_g
    if "catalog_net_price" in provided:
        product.catalog_net_price = payload.catalog_net_price
    if "unit_count" in provided:
        product.unit_count = payload.unit_count
    if "warehouse" in provided:
        product.warehouse = (payload.warehouse or "").strip() or None
    if "type_code" in provided:
        product.type_code = (payload.type_code or "").strip() or None
    if "purchase_price" in provided:
        product.purchase_price = payload.purchase_price
    if "family_code" in provided:
        product.family_code = (payload.family_code or "").strip() or None
    if "weight" in provided:
        product.weight = payload.weight
    if "package_weight" in provided:
        product.package_weight = payload.package_weight
    if "min_unit" in provided:
        product.min_unit = payload.min_unit
    if "note" in provided:
        product.note = (payload.note or "").strip() or None
    if "salon_sale_price" in provided:
        product.salon_sale_price = payload.salon_sale_price
    if "purchase_price_c" in provided:
        product.purchase_price_c = payload.purchase_price_c
    if "is_locked" in provided and payload.is_locked is not None:
        product.is_locked = payload.is_locked
    if "sale_price_gross" in provided:
        product.sale_price_gross = payload.sale_price_gross
    if "s_u" in provided and payload.s_u is not None:
        product.s_u = payload.s_u
    if "is_active" in provided and payload.is_active is not None:
        product.is_active = payload.is_active

    db.commit()
    db.refresh(product)
    salon = db.query(Salon).order_by(Salon.id.asc()).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    return _product_to_read(product, salon)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.is_active = False
    db.commit()
    return None
