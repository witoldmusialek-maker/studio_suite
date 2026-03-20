"""
CRUD endpoints for salons, staff and salon product catalog.
"""
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import File, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.salon_core import (
    LegacyVisitDocumentLine,
    LegacyWorkerCard,
    LegacyProductCatalogItem,
    Salon,
    SalonProductTargetStock,
    StaffMember,
    StaffSalonMembership,
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


DISALLOWED_ROLE_CODES = {"INNY", "TECHNIK", "EMPLOYEE", "ADMINISTRATOR"}
DISALLOWED_ROLE_NAMES = {"inny", "technik", "employee", "administrator"}
PHOTO_MAX_BYTES = 2 * 1024 * 1024
PHOTO_MAX_DIMENSION = 3000
PHOTO_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
PHOTO_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
PHOTO_MIME_BY_FORMAT = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def _ensure_admin_or_manager(current_user: User) -> None:
    if current_user.role.value not in {"admin", "manager", "manager_main", "manager_salon"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _is_two_word_name(name: str) -> bool:
    tokens = [token for token in (name or "").strip().split() if token]
    return 1 <= len(tokens) <= 2


def _is_disallowed_staff_role(role: StaffRole) -> bool:
    code = (role.code or "").strip().upper()
    name = (role.name or "").strip().lower()
    return code in DISALLOWED_ROLE_CODES or name in DISALLOWED_ROLE_NAMES


def _staff_to_read(
    staff: StaffMember,
    salons_by_id: dict[int, Salon],
    roles_by_id: dict[int, StaffRole],
    users_by_id: dict[int, User],
) -> StaffRead:
    salon = salons_by_id.get(staff.salon_id) if staff.salon_id else None
    role = roles_by_id.get(staff.role_id) if staff.role_id else None
    linked_user = users_by_id.get(staff.user_id) if staff.user_id else None
    return StaffRead(
        id=staff.id,
        display_name=staff.display_name,
        salon_id=staff.salon_id,
        salon_name=salon.name if salon else None,
        role_id=staff.role_id,
        role_name=role.name if role else None,
        user_id=staff.user_id,
        login_username=linked_user.username if linked_user else None,
        login_role=linked_user.role.value if linked_user else None,
        is_active=bool(staff.is_active),
        legacy_code=staff.legacy_code,
        public_bio=staff.public_bio,
        public_photo_url=staff.public_photo_url,
        public_photo_preview_url=(
            f"/api/v1/resources/staff/{staff.id}/photo"
            if staff.public_photo_data
            else (staff.public_photo_url or None)
        ),
        public_photo_has_blob=bool(staff.public_photo_data),
    )


def _validate_and_normalize_photo(file: UploadFile, raw: bytes) -> tuple[bytes, str]:
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plik zdjęcia jest pusty")
    if len(raw) > PHOTO_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Zdjęcie przekracza limit 2 MB")
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in PHOTO_ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Dozwolone formaty: JPG, PNG, WEBP")
    try:
        with Image.open(BytesIO(raw)) as image:
            image_format = (image.format or "").upper()
            width, height = image.size
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nieprawidłowy plik obrazu") from exc
    if image_format not in PHOTO_ALLOWED_FORMATS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Dozwolone formaty: JPG, PNG, WEBP")
    if width <= 0 or height <= 0 or width > PHOTO_MAX_DIMENSION or height > PHOTO_MAX_DIMENSION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maksymalny rozmiar zdjęcia to 3000x3000 px")
    normalized_content_type = PHOTO_MIME_BY_FORMAT.get(image_format, content_type or "image/jpeg")
    return raw, normalized_content_type


def _ensure_user_link_valid(
    db: Session,
    tenant_id: int,
    user_id: int | None,
    current_staff_id: int | None = None,
) -> None:
    if user_id is None:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = db.query(StaffMember).filter(StaffMember.user_id == user_id, StaffMember.tenant_id == tenant_id).first()
    if existing and existing.id != current_staff_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login account is already linked to another employee")


def _legacy_stock_100_for_salon(salon: Salon, product: LegacyProductCatalogItem) -> float | None:
    code = (salon.code or "").strip()
    name = (salon.name or "").strip().lower()
    if code == "05" or "pulaw" in name:
        return float(product.stock_mx03) if product.stock_mx03 is not None else None
    if code == "12" or "kras" in name:
        return float(product.stock_mx04) if product.stock_mx04 is not None else None
    if code == "07" or "odyn" in name:
        return float(product.stock_mx07) if product.stock_mx07 is not None else None
    return float(product.stock_mx04) if product.stock_mx04 is not None else None


def _stock_100_for_salon(
    salon: Salon,
    product: LegacyProductCatalogItem,
    target_by_product_id: dict[int, float] | None = None,
) -> float | None:
    if target_by_product_id is not None and product.id in target_by_product_id:
        return target_by_product_id[product.id]
    return _legacy_stock_100_for_salon(salon, product)


def _set_stock_100_for_salon(salon: Salon, product: LegacyProductCatalogItem, value: float | None) -> None:
    if value is None:
        return
    code = (salon.code or "").strip()
    name = (salon.name or "").strip().lower()
    if code == "05" or "pulaw" in name:
        product.stock_mx03 = value
        return
    if code == "12" or "kras" in name:
        product.stock_mx04 = value
        return
    if code == "07" or "odyn" in name:
        product.stock_mx07 = value
        return
    product.stock_mx04 = value


def _set_target_stock_for_salon(db: Session, salon_id: int, product_id: int, value: float | None) -> None:
    if value is None:
        return
    row = (
        db.query(SalonProductTargetStock)
        .filter(
            SalonProductTargetStock.salon_id == salon_id,
            SalonProductTargetStock.product_id == product_id,
        )
        .first()
    )
    if row is None:
        row = SalonProductTargetStock(
            salon_id=salon_id,
            product_id=product_id,
            target_quantity=value,
        )
        db.add(row)
    else:
        row.target_quantity = value


def _load_target_stock_map(db: Session, salon_id: int) -> dict[int, float]:
    rows = (
        db.query(SalonProductTargetStock)
        .filter(SalonProductTargetStock.salon_id == salon_id)
        .all()
    )
    return {
        row.product_id: float(row.target_quantity)
        for row in rows
        if row.target_quantity is not None
    }


def _generate_next_legacy_code(db: Session) -> str:
    rows = db.query(LegacyProductCatalogItem.legacy_code).all()
    max_code = 60000
    for (code,) in rows:
        if not code:
            continue
        c = str(code).strip()
        if c.isdigit():
            max_code = max(max_code, int(c))
    return str(max_code + 1)


def _product_to_read(
    product: LegacyProductCatalogItem,
    salon: Salon,
    target_by_product_id: dict[int, float] | None = None,
) -> ProductRead:
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
        stock_100=_stock_100_for_salon(salon, product, target_by_product_id),
        is_active=bool(product.is_active),
    )


@router.get("/salons", response_model=list[SalonRead])
async def list_salons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).order_by(Salon.name.asc()).all()


@router.post("/salons", response_model=SalonRead, status_code=status.HTTP_201_CREATED)
async def create_salon(
    payload: SalonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    code = payload.code.strip().upper()
    name = payload.name.strip()
    if db.query(Salon).filter(Salon.code == code, Salon.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Salon code already exists")
    row = Salon(tenant_id=current_user.tenant_id, code=code, name=name, is_active=payload.is_active)
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
    row = db.query(Salon).filter(Salon.id == salon_id, Salon.tenant_id == current_user.tenant_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.code is not None:
        code = payload.code.strip().upper()
        existing = db.query(Salon).filter(
            Salon.code == code,
            Salon.id != salon_id,
            Salon.tenant_id == current_user.tenant_id,
        ).first()
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
    row = db.query(Salon).filter(Salon.id == salon_id, Salon.tenant_id == current_user.tenant_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    db.query(StaffMember).filter(
        StaffMember.salon_id == salon_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).update({StaffMember.salon_id: None})
    db.delete(row)
    db.commit()
    return None


@router.get("/functions", response_model=list[StaffFunctionRead])
async def list_staff_functions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(StaffRole).order_by(StaffRole.name.asc()).all()
    return [row for row in rows if not _is_disallowed_staff_role(row)]


@router.get("/staff", response_model=list[StaffRead])
async def list_staff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff_rows = db.query(StaffMember).filter(StaffMember.tenant_id == current_user.tenant_id).order_by(StaffMember.display_name.asc()).all()
    staff_rows = [row for row in staff_rows if _is_two_word_name(row.display_name)]
    salons = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()
    roles = db.query(StaffRole).all()
    users = db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
    salons_by_id = {row.id: row for row in salons}
    roles_by_id = {row.id: row for row in roles}
    users_by_id = {row.id: row for row in users}
    return [_staff_to_read(row, salons_by_id, roles_by_id, users_by_id) for row in staff_rows]


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    if not _is_two_word_name(payload.display_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pracownik musi miec imie i nazwisko (max 2 wyrazy)")
    if payload.salon_id is not None and not db.query(Salon).filter(Salon.id == payload.salon_id, Salon.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.role_id is not None:
        role = db.query(StaffRole).filter(StaffRole.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")
        if _is_disallowed_staff_role(role):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wybrana funkcja jest niedozwolona")
    _ensure_user_link_valid(db, current_user.tenant_id, payload.user_id)

    row = StaffMember(
        tenant_id=current_user.tenant_id,
        display_name=payload.display_name.strip(),
        legacy_code=(payload.legacy_code or "").strip() or None,
        public_bio=(payload.public_bio or "").strip() or None,
        public_photo_url=(payload.public_photo_url or "").strip() or None,
        salon_id=payload.salon_id,
        role_id=payload.role_id,
        user_id=payload.user_id,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    users_by_id = {item.id: item for item in db.query(User).filter(User.tenant_id == current_user.tenant_id).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id, users_by_id)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(
        StaffMember.id == staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    provided = payload.model_fields_set

    if "display_name" in provided and payload.display_name is not None and not _is_two_word_name(payload.display_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pracownik musi miec imie i nazwisko (max 2 wyrazy)")
    if "salon_id" in provided and payload.salon_id is not None and not db.query(Salon).filter(
        Salon.id == payload.salon_id,
        Salon.tenant_id == current_user.tenant_id,
    ).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if "role_id" in provided and payload.role_id is not None:
        role = db.query(StaffRole).filter(StaffRole.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")
        if _is_disallowed_staff_role(role):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wybrana funkcja jest niedozwolona")
    if "user_id" in provided:
        _ensure_user_link_valid(db, current_user.tenant_id, payload.user_id, current_staff_id=row.id)

    if "display_name" in provided and payload.display_name is not None:
        row.display_name = payload.display_name.strip()
    if "legacy_code" in provided:
        row.legacy_code = (payload.legacy_code or "").strip() or None
    if "public_bio" in provided:
        row.public_bio = (payload.public_bio or "").strip() or None
    if "public_photo_url" in provided:
        row.public_photo_url = (payload.public_photo_url or "").strip() or None
    if "salon_id" in provided:
        row.salon_id = payload.salon_id
    if "role_id" in provided:
        row.role_id = payload.role_id
    if "user_id" in provided:
        row.user_id = payload.user_id
    if "is_active" in provided and payload.is_active is not None:
        row.is_active = payload.is_active

    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    users_by_id = {item.id: item for item in db.query(User).filter(User.tenant_id == current_user.tenant_id).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id, users_by_id)


@router.get("/staff/{staff_id}/photo")
async def get_staff_photo(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(StaffMember).filter(
        StaffMember.id == staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first()
    if not row or not row.public_photo_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zdjęcie pracownika nie istnieje")
    return Response(content=bytes(row.public_photo_data), media_type=row.public_photo_content_type or "image/jpeg")


@router.post("/staff/{staff_id}/photo", response_model=StaffRead)
async def upload_staff_photo(
    staff_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(
        StaffMember.id == staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    raw = await file.read()
    image_data, content_type = _validate_and_normalize_photo(file, raw)
    row.public_photo_data = image_data
    row.public_photo_content_type = content_type
    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    users_by_id = {item.id: item for item in db.query(User).filter(User.tenant_id == current_user.tenant_id).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id, users_by_id)


@router.delete("/staff/{staff_id}/photo", response_model=StaffRead)
async def delete_staff_photo(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(
        StaffMember.id == staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    row.public_photo_data = None
    row.public_photo_content_type = None
    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    users_by_id = {item.id: item for item in db.query(User).filter(User.tenant_id == current_user.tenant_id).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id, users_by_id)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(
        StaffMember.id == staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    # Soft delete: hide from operational views (calendar/staff lists),
    # keep historical/accounting consistency and avoid FK deletion failures.
    row.is_active = False
    row.can_be_booked = False
    row.salon_id = None
    row.user_id = None

    db.query(StaffSalonMembership).filter(StaffSalonMembership.staff_id == staff_id).update(
        {StaffSalonMembership.is_active: False}
    )
    db.query(LegacyWorkerCard).filter(LegacyWorkerCard.mapped_staff_id == staff_id).update(
        {LegacyWorkerCard.mapped_staff_id: None}
    )
    db.query(LegacyVisitDocumentLine).filter(LegacyVisitDocumentLine.mapped_staff_id == staff_id).update(
        {LegacyVisitDocumentLine.mapped_staff_id: None}
    )
    db.commit()
    return None


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    salon = db.query(Salon).filter(
        Salon.id == salon_id,
        Salon.tenant_id == current_user.tenant_id,
    ).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")

    products = db.query(LegacyProductCatalogItem).order_by(LegacyProductCatalogItem.legacy_code.asc()).all()
    target_by_product_id = _load_target_stock_map(db, salon.id)
    out: list[ProductRead] = []
    for product in products:
        out.append(_product_to_read(product, salon, target_by_product_id))
    out.sort(key=lambda item: item.product_code)
    return out


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    salons = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).order_by(Salon.id.asc()).all()
    if not salons:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    salon = salons[0]
    if payload.salon_id is not None:
        selected = db.query(Salon).filter(
            Salon.id == payload.salon_id,
            Salon.tenant_id == current_user.tenant_id,
        ).first()
        if not selected:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        salon = selected

    code = (payload.product_code or "").strip().upper() or _generate_next_legacy_code(db)
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
    _set_stock_100_for_salon(salon, product, payload.stock_100)
    _set_target_stock_for_salon(db, salon.id, product.id, payload.stock_100)

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
    salon = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).order_by(Salon.id.asc()).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.salon_id is not None:
        selected = db.query(Salon).filter(
            Salon.id == payload.salon_id,
            Salon.tenant_id == current_user.tenant_id,
        ).first()
        if not selected:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
        salon = selected
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
    if "stock_100" in provided:
        _set_stock_100_for_salon(salon, product, payload.stock_100)
        _set_target_stock_for_salon(db, salon.id, product.id, payload.stock_100)

    db.commit()
    db.refresh(product)
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
