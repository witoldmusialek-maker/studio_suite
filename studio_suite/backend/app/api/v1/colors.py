"""Color and product-family dictionary API."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, not_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.salon_core import LegacyProductCatalogItem, ProductFamilyDictionary
from app.models.user import User, UserRole
from app.schemas.resources import (
    ColorDetailRead,
    ColorFamilyRead,
    ColorRead,
    ProductFamilyDictionaryCreate,
    ProductFamilyDictionaryRead,
    ProductFamilyDictionaryUpdate,
)

router = APIRouter(tags=["colors"])

BACKBAR_FISCAL_CODES = ("01000", "02000", "02200", "05000")


def _apply_backbar_filter(query):
    fiscal_code = func.coalesce(LegacyProductCatalogItem.fiscal_code, "")
    query = query.filter(
        or_(
            fiscal_code.in_(BACKBAR_FISCAL_CODES),
            fiscal_code.ilike("000%"),
            fiscal_code == "",
        )
    )
    query = query.filter(
        not_(
            or_(
                func.coalesce(LegacyProductCatalogItem.family_code, "").ilike("%SPRZEDA%"),
                func.coalesce(LegacyProductCatalogItem.name, "").ilike("%SPRZEDAŻ%"),
                func.coalesce(LegacyProductCatalogItem.name, "").ilike("%SPRZEDAZ%"),
                func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike("%SPRZEDAŻ%"),
                func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike("%SPRZEDAZ%"),
            )
        )
    )
    return query


def _apply_sales_and_service_exclusions(query):
    return query.filter(
        not_(
            or_(
                func.coalesce(LegacyProductCatalogItem.name, "").ilike("%USUGA%"),
                func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike("%USUGA%"),
                func.coalesce(LegacyProductCatalogItem.family_code, "").ilike("%SPRZEDA%"),
                func.coalesce(LegacyProductCatalogItem.name, "").ilike("%SPRZEDAŻ%"),
                func.coalesce(LegacyProductCatalogItem.name, "").ilike("%SPRZEDAZ%"),
                func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike("%SPRZEDAŻ%"),
                func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike("%SPRZEDAZ%"),
            )
        )
    )


def _require_family_editor(current_user: User):
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role not in {UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.MANAGER_MAIN.value, UserRole.MANAGER_SALON.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _base_products_query(db: Session, backbar: bool):
    query = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.is_active.is_(True))
    if backbar:
        query = _apply_backbar_filter(query)
    return _apply_sales_and_service_exclusions(query)


def _load_dictionary_row(db: Session, family_token: str) -> ProductFamilyDictionary | None:
    token = family_token.strip()
    if not token:
        return None
    return (
        db.query(ProductFamilyDictionary)
        .filter(
            ProductFamilyDictionary.is_active.is_(True),
            or_(
                func.lower(ProductFamilyDictionary.code) == token.lower(),
                func.lower(ProductFamilyDictionary.name) == token.lower(),
            ),
        )
        .first()
    )


def _distinct_legacy_families(db: Session, backbar: bool) -> list[tuple[str, int]]:
    base_query = _base_products_query(db, backbar=backbar)
    family_expr = func.trim(func.coalesce(LegacyProductCatalogItem.family_code, ""))
    rows = (
        base_query.with_entities(
            family_expr.label("family"),
            func.count(LegacyProductCatalogItem.id).label("product_count"),
        )
        .filter(family_expr != "")
        .group_by(family_expr)
        .order_by(family_expr.asc())
        .all()
    )
    return [(row.family, int(row.product_count or 0)) for row in rows]


def _distinct_product_families_without_fiscal(db: Session) -> list[tuple[str, int]]:
    family_expr = func.trim(func.coalesce(LegacyProductCatalogItem.family_code, ""))
    fiscal_code = func.trim(func.coalesce(LegacyProductCatalogItem.fiscal_code, ""))
    rows = (
        db.query(
            family_expr.label("family"),
            func.count(LegacyProductCatalogItem.id).label("product_count"),
        )
        .filter(
            LegacyProductCatalogItem.is_active.is_(True),
            family_expr != "",
            fiscal_code == "",
        )
        .group_by(family_expr)
        .order_by(family_expr.asc())
        .all()
    )
    return [(row.family, int(row.product_count or 0)) for row in rows]


@router.post("/colors/family-dicts/import-legacy", response_model=list[ProductFamilyDictionaryRead])
async def import_family_dictionaries_from_legacy(
    replace: bool = Query(default=True),
    backbar: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_family_editor(current_user)
    if replace:
        db.query(ProductFamilyDictionary).delete()
        db.commit()

    existing = {
        row.code.lower(): row
        for row in db.query(ProductFamilyDictionary).all()
    }
    imported: list[ProductFamilyDictionaryRead] = []
    for index, (family_name, product_count) in enumerate(_distinct_legacy_families(db, backbar=backbar), start=1):
        key = family_name.lower()
        row = existing.get(key)
        if row is None:
            row = ProductFamilyDictionary(
                code=family_name,
                name=family_name,
                description="Zaimportowano z legacy",
                sort_order=index * 10,
                is_active=True,
            )
            db.add(row)
            db.flush()
            existing[key] = row
        else:
            row.name = family_name
            if row.sort_order is None:
                row.sort_order = index * 10
        imported.append(
            ProductFamilyDictionaryRead(
                id=row.id,
                code=row.code,
                name=row.name,
                description=row.description,
                sort_order=row.sort_order,
                is_active=row.is_active,
                product_count=product_count,
            )
        )
    db.commit()
    return imported


@router.get("/colors/family-dicts", response_model=list[ProductFamilyDictionaryRead])
async def list_family_dictionaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    count_by_code = {family: count for family, count in _distinct_legacy_families(db, backbar=True)}
    rows = (
        db.query(ProductFamilyDictionary)
        .order_by(ProductFamilyDictionary.sort_order.asc(), ProductFamilyDictionary.name.asc())
        .all()
    )
    return [
        ProductFamilyDictionaryRead(
            id=row.id,
            code=row.code,
            name=row.name,
            description=row.description,
            sort_order=row.sort_order,
            is_active=row.is_active,
            product_count=count_by_code.get(row.code, 0),
        )
        for row in rows
    ]


@router.post("/colors/family-dicts", response_model=ProductFamilyDictionaryRead, status_code=status.HTTP_201_CREATED)
async def create_family_dictionary(
    payload: ProductFamilyDictionaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_family_editor(current_user)
    item = ProductFamilyDictionary(
        code=payload.code.strip(),
        name=payload.name.strip(),
        description=(payload.description or "").strip() or None,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Family code already exists")
    db.refresh(item)
    return ProductFamilyDictionaryRead(
        id=item.id,
        code=item.code,
        name=item.name,
        description=item.description,
        sort_order=item.sort_order,
        is_active=item.is_active,
        product_count=0,
    )


@router.patch("/colors/family-dicts/{family_id}", response_model=ProductFamilyDictionaryRead)
async def update_family_dictionary(
    family_id: int,
    payload: ProductFamilyDictionaryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_family_editor(current_user)
    item = db.query(ProductFamilyDictionary).filter(ProductFamilyDictionary.id == family_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    if payload.code is not None:
        item.code = payload.code.strip()
    if payload.name is not None:
        item.name = payload.name.strip()
    if payload.description is not None:
        item.description = payload.description.strip() or None
    if payload.sort_order is not None:
        item.sort_order = payload.sort_order
    if payload.is_active is not None:
        item.is_active = payload.is_active
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Family code already exists")
    db.refresh(item)
    product_count = dict(_distinct_legacy_families(db, backbar=True)).get(item.code, 0)
    return ProductFamilyDictionaryRead(
        id=item.id,
        code=item.code,
        name=item.name,
        description=item.description,
        sort_order=item.sort_order,
        is_active=item.is_active,
        product_count=product_count,
    )


@router.delete("/colors/family-dicts/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_dictionary(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_family_editor(current_user)
    item = db.query(ProductFamilyDictionary).filter(ProductFamilyDictionary.id == family_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    db.delete(item)
    db.commit()


@router.get("/colors/families", response_model=list[ColorFamilyRead])
async def list_color_families(
    backbar: bool = Query(default=False),
    raw: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    del raw
    count_by_code = {family: count for family, count in _distinct_legacy_families(db, backbar=backbar)}
    rows = (
        db.query(ProductFamilyDictionary)
        .filter(ProductFamilyDictionary.is_active.is_(True))
        .order_by(ProductFamilyDictionary.sort_order.asc(), ProductFamilyDictionary.name.asc())
        .all()
    )
    if rows:
        return [
            ColorFamilyRead(
                id=row.id,
                value=row.code,
                label=row.name,
                product_count=count_by_code.get(row.code, 0),
            )
            for row in rows
        ]

    distinct_legacy = _distinct_product_families_without_fiscal(db)
    return [
        ColorFamilyRead(
            id=None,
            value=name,
            label=name,
            product_count=count,
        )
        for name, count in distinct_legacy
    ]


@router.get("/colors", response_model=list[ColorRead])
async def list_colors(
    family: str | None = Query(default=None),
    search: str | None = Query(default=None),
    backbar: bool = Query(default=False),
    salon_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    del salon_id

    query = _base_products_query(db, backbar=backbar)
    if family:
        token = family.strip()
        if token:
            dictionary_row = _load_dictionary_row(db, token)
            normalized_family = dictionary_row.code if dictionary_row else token.replace("_", " ").replace("-", " ")
            query = query.filter(
                func.trim(func.coalesce(LegacyProductCatalogItem.family_code, "")).ilike(normalized_family)
            )
    if search:
        token = search.strip()
        if token:
            like = f"%{token}%"
            query = query.filter(
                or_(
                    func.coalesce(LegacyProductCatalogItem.legacy_code, "").ilike(like),
                    func.coalesce(LegacyProductCatalogItem.name, "").ilike(like),
                    func.coalesce(LegacyProductCatalogItem.name_pl, "").ilike(like),
                    func.coalesce(LegacyProductCatalogItem.brand_1, "").ilike(like),
                    func.coalesce(LegacyProductCatalogItem.brand_2, "").ilike(like),
                )
            )

    rows = query.order_by(LegacyProductCatalogItem.legacy_code.asc(), LegacyProductCatalogItem.name.asc()).all()
    return [
        ColorRead(
            id=row.id,
            code=row.legacy_code,
            name=row.name,
            family_code=row.family_code,
            brand=row.brand_1 or row.brand_2 or None,
        )
        for row in rows
    ]


def _format_decimal(value: float | None) -> str | None:
    if value is None:
        return None
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):g}"


@router.get("/colors/{product_id}", response_model=ColorDetailRead)
async def get_color_detail(
    product_id: int,
    backbar: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user

    row = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == product_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if backbar:
        family_code = (row.family_code or "").upper()
        name = (row.name or "").upper()
        name_pl = (row.name_pl or "").upper()
        fiscal_code = (row.fiscal_code or "").strip()
        is_backbar = (
            fiscal_code in BACKBAR_FISCAL_CODES
            or fiscal_code.startswith("000")
            or fiscal_code == ""
        )
        is_sales = "SPRZEDA" in family_code or "SPRZEDA" in name or "SPRZEDA" in name_pl
        if not is_backbar or is_sales:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not available for backbar")

    package_value = float(row.quantity) if row.quantity is not None else None
    poj = f"{_format_decimal(package_value)} ml" if package_value is not None else None
    iljedn = "1 szt"
    return ColorDetailRead(
        id=row.id,
        code=row.legacy_code,
        name=row.name,
        family_code=row.family_code,
        brand=row.brand_1 or row.brand_2 or None,
        poj=poj,
        iljedn=iljedn,
    )
