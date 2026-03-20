"""Inventory API."""
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    InventoryIssue,
    InventoryIssueLine,
    LegacyProductCatalogItem,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceipt,
    GoodsReceiptLine,
    ReplenishmentSuggestion,
    SalonProductTargetStock,
    ServiceCatalogItem,
    ServiceRecipeItem,
    StaffMember,
    StockLevel,
    StockLocation,
)
from app.models.user import User, UserRole
from app.schemas.inventory import (
    GoodsReceiptCreate,
    GoodsReceiptLineRead,
    GoodsReceiptRead,
    InventoryDailyOutflowSummaryRead,
    InventoryIssueCreate,
    InventoryIssueLineRead,
    InventoryIssueRead,
    InventoryIssueUpdate,
    PurchaseOrderCreate,
    PurchaseOrderLineRead,
    PurchaseOrderRead,
    ReplenishmentSuggestionRead,
    StockAdjustmentDeltaCreate,
    StockAdjustmentStocktakeCreate,
    StocktakeCandidateRead,
    StockLevelRead,
    StockLocationCreate,
    StockLocationRead,
)
from scripts.import_legacy_stock_reports import apply_stock_levels_from_latest_rem_table, run_import

router = APIRouter(prefix="/inventory", tags=["inventory"])


MANAGER_ROLES = {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}


def _is_manager_role(user: User) -> bool:
    return user.role in MANAGER_ROLES


def _can_manage_all_salons(user: User) -> bool:
    return user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN}


def _allowed_salons_for_user(db: Session, current_user: User, current_staff: StaffMember | None) -> set[int] | None:
    if _can_manage_all_salons(current_user):
        return None
    allowed = get_staff_allowed_salons(db, current_staff)
    return allowed


def _ensure_inventory_write_access(
    db: Session,
    current_user: User,
    current_staff: StaffMember | None,
    salon_id: int,
    payload_staff_id: int | None,
) -> int | None:
    require_salon_access(db, current_user, salon_id)
    if current_user.role in {UserRole.ADMIN, UserRole.RECEPTIONIST} or _is_manager_role(current_user):
        return payload_staff_id
    if current_user.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if current_staff is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
    if payload_staff_id is not None and payload_staff_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee can register issue only for self")
    return current_staff.id


def _decimal_or_none(value: float | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _recompute_replenishment_for_salon(
    db: Session,
    salon_id: int,
    only_product_ids: set[int] | None = None,
) -> list[ReplenishmentSuggestion]:
    target_rows = (
        db.query(SalonProductTargetStock)
        .filter(SalonProductTargetStock.salon_id == salon_id)
        .all()
    )
    if only_product_ids is not None:
        target_rows = [row for row in target_rows if row.product_id in only_product_ids]
    if not target_rows:
        return []

    product_ids = {row.product_id for row in target_rows}
    if not product_ids:
        return []

    level_rows = (
        db.query(
            StockLevel.product_id,
            StockLevel.quantity,
            StockLocation.location_type,
        )
        .join(StockLocation, StockLocation.id == StockLevel.stock_location_id)
        .filter(
            StockLocation.salon_id == salon_id,
            StockLocation.is_active.is_(True),
            StockLevel.product_id.in_(product_ids),
        )
        .all()
    )
    actual_by_product: dict[int, Decimal] = {}
    for row in level_rows:
        # Target stock is operational (service/backbar), so retail-only stock is excluded.
        if (row.location_type or "").upper() == "RETAIL":
            continue
        actual_by_product[row.product_id] = actual_by_product.get(row.product_id, Decimal("0")) + Decimal(str(row.quantity or 0))

    existing_open = (
        db.query(ReplenishmentSuggestion)
        .filter(
            ReplenishmentSuggestion.salon_id == salon_id,
            ReplenishmentSuggestion.status == "OPEN",
        )
        .all()
    )
    existing_by_product = {row.product_id: row for row in existing_open}
    touched_open_ids: set[int] = set()
    generated: list[ReplenishmentSuggestion] = []

    for target in target_rows:
        target_qty = Decimal(str(target.target_quantity or 0))
        actual_qty = actual_by_product.get(target.product_id, Decimal("0"))
        deficit = target_qty - actual_qty
        row = existing_by_product.get(target.product_id)
        if target_qty > Decimal("0") and deficit > Decimal("0"):
            if row is None:
                row = ReplenishmentSuggestion(
                    salon_id=salon_id,
                    product_id=target.product_id,
                    target_quantity=target_qty,
                    actual_quantity=actual_qty,
                    suggested_quantity=deficit,
                    status="OPEN",
                )
                db.add(row)
                db.flush()
            else:
                row.target_quantity = target_qty
                row.actual_quantity = actual_qty
                row.suggested_quantity = deficit
                row.status = "OPEN"
                row.resolved_at = None
            touched_open_ids.add(row.id)
            generated.append(row)
        else:
            if row is not None:
                row.target_quantity = target_qty
                row.actual_quantity = actual_qty
                row.suggested_quantity = Decimal("0")
                row.status = "CLOSED"
                row.resolved_at = func.now()

    # Keep only still-relevant OPEN rows in this cycle.
    for row in existing_open:
        if row.id not in touched_open_ids and (only_product_ids is None or row.product_id in only_product_ids):
            row.status = "CLOSED"
            row.suggested_quantity = Decimal("0")
            row.resolved_at = func.now()

    return generated


def _replenishment_to_read(
    row: ReplenishmentSuggestion,
    product_by_id: dict[int, LegacyProductCatalogItem],
) -> ReplenishmentSuggestionRead:
    return ReplenishmentSuggestionRead(
        id=row.id,
        salon_id=row.salon_id,
        product_id=row.product_id,
        product_name=product_by_id.get(row.product_id).name if row.product_id in product_by_id else None,
        target_quantity=float(row.target_quantity or 0),
        actual_quantity=float(row.actual_quantity or 0),
        suggested_quantity=float(row.suggested_quantity or 0),
        status=row.status,
        generated_at=row.generated_at,
        resolved_at=row.resolved_at,
        note=row.note,
    )


def _estimate_unit_cost(product: LegacyProductCatalogItem | None) -> Decimal:
    if product is None:
        return Decimal("0")
    for candidate in (product.purchase_price, product.purchase_price_c, product.catalog_net_price):
        if candidate is not None:
            return Decimal(str(candidate))
    return Decimal("0")


def _format_qty(value: Decimal) -> str:
    normalized = value.quantize(Decimal("0.0001"))
    text = format(normalized, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _get_or_create_stock_level(
    db: Session,
    stock_location_id: int,
    product_id: int,
) -> StockLevel:
    level = (
        db.query(StockLevel)
        .filter(
            StockLevel.stock_location_id == stock_location_id,
            StockLevel.product_id == product_id,
        )
        .first()
    )
    if level:
        return level
    level = StockLevel(
        stock_location_id=stock_location_id,
        product_id=product_id,
        quantity=Decimal("0"),
    )
    db.add(level)
    db.flush()
    return level


def _resolve_salon_stock_location(
    db: Session,
    tenant_id: int,
    salon_id: int,
    requested_location_id: int | None,
) -> StockLocation:
    if requested_location_id is not None:
        location = db.query(StockLocation).filter(
            StockLocation.id == requested_location_id,
            StockLocation.tenant_id == tenant_id,
        ).first()
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock location not found")
        if location.salon_id != salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock location does not belong to salon")
        return location

    location = (
        db.query(StockLocation)
        .filter(
            StockLocation.tenant_id == tenant_id,
            StockLocation.salon_id == salon_id,
            StockLocation.code == "SALON_GLOWNY",
        )
        .first()
    )
    if location is None:
        location = (
            db.query(StockLocation)
            .filter(
                StockLocation.tenant_id == tenant_id,
                StockLocation.salon_id == salon_id,
                StockLocation.is_active.is_(True),
            )
            .order_by(StockLocation.id.asc())
            .first()
        )
    if location is None:
        location = StockLocation(
            tenant_id=tenant_id,
            salon_id=salon_id,
            code="SALON_GLOWNY",
            name="Salon główny",
            location_type="MIXED",
            is_active=True,
        )
        db.add(location)
        db.flush()
    return location


@router.post("/legacy-stock/import", status_code=status.HTTP_201_CREATED)
async def import_legacy_stock_archive(
    archive: UploadFile = File(...),
    apply_stock_levels: bool = Form(True),
    notes: str | None = Form(None),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    archive_name = (archive.filename or "").strip()
    if not archive_name.lower().endswith(".7z"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .7z archive is supported")

    temp_path = ""
    with tempfile.NamedTemporaryFile(prefix="legacy_stock_", suffix=".7z", delete=False) as tmp_file:
        temp_path = tmp_file.name
        tmp_file.write(await archive.read())

    try:
        import_stats = run_import(
            archive_path=Path(temp_path),
            tenant_id=current_user.tenant_id,
            notes=notes or f"uploaded by {current_user.username}",
        )
        apply_stats = None
        if apply_stock_levels:
            apply_stats = apply_stock_levels_from_latest_rem_table(
                batch_id=int(import_stats["batch_id"]),
                tenant_id=current_user.tenant_id,
                remarks_prefix=f"Legacy rem_table upload by {current_user.username}",
            )
        return {
            "ok": True,
            "import": import_stats,
            "stock_levels_applied": apply_stats,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Legacy import failed: {exc}") from exc
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


@router.get("/legacy-stock/import-required-files")
async def legacy_stock_import_required_files(
    current_user: User = Depends(get_current_user),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return {
        "archive": {
            "format": ".7z",
            "description": "One archive with legacy stock reports.",
        },
        "required_patterns": [
            "rem_tableYYYY_M_<YYYY_MM_DD-HH_MM_SS>_<Salon>.xls",
        ],
        "optional_patterns": [
            "stan_balance<Salon>DD_MM_YYYY_HH_MM.xls",
            "*.pdf",
        ],
        "notes": [
            "To apply stock levels, rem_table files are required.",
            "Product mapping uses product legacy code (idprod) -> legacy_product_catalog_items.legacy_code.",
            "If a salon has no stock location, system creates default SALON_GLOWNY automatically.",
        ],
    }


def _effective_dose_weight_raw(
    min_unit: Decimal,
    full_weight: Decimal,
    package_weight: Decimal,
    unit_count: Decimal,
) -> Decimal:
    net_weight = full_weight - package_weight
    if unit_count > Decimal("0") and net_weight > Decimal("0"):
        derived = net_weight / unit_count
        if derived > Decimal("0"):
            return derived
    return min_unit


def _measurement_mode_for_product(product: LegacyProductCatalogItem) -> str:
    dose_weight = _effective_dose_weight(product)
    has_weight_profile = product.weight is not None or product.package_weight is not None
    if dose_weight > Decimal("0") and has_weight_profile:
        return "WEIGHT"
    return "PCS"


def _effective_dose_weight(product: LegacyProductCatalogItem) -> Decimal:
    # Legacy data uses multiple conventions for min_unit. Prefer robust derivation from
    # package net weight and units-in-package when available; fallback to min_unit.
    min_unit = Decimal(str(product.min_unit or 0))
    full_weight = Decimal(str(product.weight or 0))
    package_weight = Decimal(str(product.package_weight or 0))
    unit_count = Decimal(str(product.unit_count or 0))
    return _effective_dose_weight_raw(min_unit, full_weight, package_weight, unit_count)


def _load_issue_context(
    db: Session,
    issue_ids: list[int],
) -> tuple[dict[int, list[InventoryIssueLine]], dict[int, LegacyProductCatalogItem], dict[int, ServiceRecipeItem]]:
    if not issue_ids:
        return {}, {}, {}

    lines = (
        db.query(InventoryIssueLine)
        .filter(InventoryIssueLine.inventory_issue_id.in_(issue_ids))
        .order_by(InventoryIssueLine.id.asc())
        .all()
    )
    lines_by_issue: dict[int, list[InventoryIssueLine]] = {}
    product_ids = {line.product_id for line in lines if line.product_id is not None}
    recipe_item_ids = {line.recipe_item_id for line in lines if getattr(line, "recipe_item_id", None) is not None}
    for line in lines:
        lines_by_issue.setdefault(line.inventory_issue_id, []).append(line)

    products_by_id: dict[int, LegacyProductCatalogItem] = {}
    if product_ids:
        products_by_id = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
        }

    recipe_by_id: dict[int, ServiceRecipeItem] = {}
    if recipe_item_ids:
        recipe_by_id = {
            row.id: row
            for row in db.query(ServiceRecipeItem).filter(ServiceRecipeItem.id.in_(recipe_item_ids)).all()
        }

    return lines_by_issue, products_by_id, recipe_by_id


def _issue_to_read(
    issue: InventoryIssue,
    lines: list[InventoryIssueLine],
    products_by_id: dict[int, LegacyProductCatalogItem] | None = None,
    recipe_by_id: dict[int, ServiceRecipeItem] | None = None,
) -> InventoryIssueRead:
    products_by_id = products_by_id or {}
    recipe_by_id = recipe_by_id or {}
    return InventoryIssueRead(
        id=issue.id,
        salon_id=issue.salon_id,
        stock_location_id=issue.stock_location_id,
        appointment_id=issue.appointment_id,
        service_id=issue.service_id,
        performed_line_id=issue.performed_line_id,
        staff_id=issue.staff_id,
        issue_time=issue.issue_time,
        status=issue.status,
        remarks=issue.remarks,
        lines=[
            InventoryIssueLineRead(
                id=line.id,
                recipe_item_id=line.recipe_item_id,
                recipe_product_family=recipe_by_id.get(line.recipe_item_id).product_family if line.recipe_item_id in recipe_by_id else None,
                recipe_note=recipe_by_id.get(line.recipe_item_id).note if line.recipe_item_id in recipe_by_id else None,
                product_id=line.product_id,
                product_name=products_by_id.get(line.product_id).name if line.product_id in products_by_id else None,
                appointment_id=line.appointment_id,
                service_id=line.service_id,
                performed_line_id=line.performed_line_id,
                quantity_planned=float(line.quantity_planned) if line.quantity_planned is not None else None,
                quantity_actual=float(line.quantity_actual) if line.quantity_actual is not None else None,
                unit=line.unit,
                unit_cost=float(line.unit_cost),
                total_cost=float(line.total_cost),
            )
            for line in lines
        ],
    )


def _get_issue_or_404(db: Session, issue_id: int, tenant_id: int) -> InventoryIssue:
    issue = db.query(InventoryIssue).filter(
        InventoryIssue.id == issue_id,
        InventoryIssue.tenant_id == tenant_id,
    ).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.get("/stock-locations", response_model=list[StockLocationRead])
async def list_stock_locations(
    salon_id: int | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = db.query(StockLocation).filter(StockLocation.tenant_id == current_user.tenant_id)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(StockLocation.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(StockLocation.salon_id.in_(allowed))
    rows = query.order_by(StockLocation.salon_id.asc(), StockLocation.code.asc()).all()
    return [
        StockLocationRead(
            id=row.id,
            salon_id=row.salon_id,
            code=row.code,
            name=row.name,
            location_type=row.location_type,
            is_active=bool(row.is_active),
        )
        for row in rows
    ]


@router.post("/stock-locations", response_model=StockLocationRead, status_code=status.HTTP_201_CREATED)
async def create_stock_location(
    payload: StockLocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/manager can create stock locations")
    require_salon_access(db, current_user, payload.salon_id)
    existing = (
        db.query(StockLocation)
        .filter(StockLocation.salon_id == payload.salon_id, StockLocation.code == payload.code.strip().upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock location code already exists in salon")
    row = StockLocation(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        location_type=payload.location_type.strip().upper(),
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return StockLocationRead(
        id=row.id,
        salon_id=row.salon_id,
        code=row.code,
        name=row.name,
        location_type=row.location_type,
        is_active=bool(row.is_active),
    )


@router.get("/stock-levels", response_model=list[StockLevelRead])
async def list_stock_levels(
    salon_id: int | None = None,
    location_id: int | None = None,
    product_id: int | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = (
        db.query(
            StockLevel,
            StockLocation.name.label("stock_location_name"),
            StockLocation.salon_id.label("salon_id"),
            LegacyProductCatalogItem.legacy_code.label("product_code"),
            LegacyProductCatalogItem.name.label("product_name"),
            LegacyProductCatalogItem.brand_1.label("brand_1"),
            LegacyProductCatalogItem.brand_2.label("brand_2"),
            LegacyProductCatalogItem.family_code.label("family_code"),
            LegacyProductCatalogItem.is_active.label("is_active"),
            LegacyProductCatalogItem.min_unit.label("product_min_unit"),
            LegacyProductCatalogItem.weight.label("product_full_weight"),
            LegacyProductCatalogItem.package_weight.label("product_package_weight"),
            LegacyProductCatalogItem.unit_count.label("product_unit_count"),
            SalonProductTargetStock.target_quantity.label("target_stock_100"),
        )
        .join(StockLocation, StockLocation.id == StockLevel.stock_location_id)
        .join(LegacyProductCatalogItem, LegacyProductCatalogItem.id == StockLevel.product_id)
        .outerjoin(
            SalonProductTargetStock,
            (
                (SalonProductTargetStock.salon_id == StockLocation.salon_id)
                & (SalonProductTargetStock.product_id == StockLevel.product_id)
            ),
        )
        .filter(StockLocation.tenant_id == current_user.tenant_id)
    )
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(StockLocation.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(StockLocation.salon_id.in_(allowed))
    if location_id is not None:
        location = db.query(StockLocation).filter(
            StockLocation.id == location_id,
            StockLocation.tenant_id == current_user.tenant_id,
        ).first()
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock location not found")
        require_salon_access(db, current_user, location.salon_id)
        query = query.filter(StockLevel.stock_location_id == location_id)
    if product_id is not None:
        query = query.filter(StockLevel.product_id == product_id)
    rows = query.order_by(StockLevel.stock_location_id.asc(), StockLevel.product_id.asc()).all()
    return [
        (
            (lambda base_qty, dose_weight, net_package_weight, unit_count, is_weight_mode: StockLevelRead(
                id=row.StockLevel.id,
                stock_location_id=row.StockLevel.stock_location_id,
                stock_location_name=row.stock_location_name,
                salon_id=row.salon_id,
                product_id=row.StockLevel.product_id,
                product_code=row.product_code,
                product_name=row.product_name,
                brand=(row.brand_1 or row.brand_2),
                family_code=row.family_code,
                is_active=bool(row.is_active) if row.is_active is not None else True,
                target_stock_100=float(row.target_stock_100) if row.target_stock_100 is not None else None,
                quantity=float(base_qty * dose_weight) if is_weight_mode else float(base_qty),
                unit=("G" if is_weight_mode else "PCS"),
                quantity_base=float(base_qty),
                unit_base=("DOSE" if is_weight_mode else "PCS"),
                unit_count=float(unit_count) if unit_count > Decimal("0") else None,
                dose_weight=float(dose_weight) if dose_weight > Decimal("0") else None,
                package_net_weight=float(net_package_weight) if net_package_weight > Decimal("0") else None,
            ))(
                Decimal(str(row.StockLevel.quantity or 0)),
                _effective_dose_weight_raw(
                    Decimal(str(row.product_min_unit or 0)),
                    Decimal(str(row.product_full_weight or 0)),
                    Decimal(str(row.product_package_weight or 0)),
                    Decimal(str(row.product_unit_count or 0)),
                ),
                (Decimal(str(row.product_full_weight or 0)) - Decimal(str(row.product_package_weight or 0))),
                Decimal(str(row.product_unit_count or 0)),
                _effective_dose_weight_raw(
                    Decimal(str(row.product_min_unit or 0)),
                    Decimal(str(row.product_full_weight or 0)),
                    Decimal(str(row.product_package_weight or 0)),
                    Decimal(str(row.product_unit_count or 0)),
                ) > Decimal("0")
                and ((row.product_full_weight is not None) or (row.product_package_weight is not None)),
            )
        )
        for row in rows
    ]


@router.get("/stocktake-candidates", response_model=list[StocktakeCandidateRead])
async def list_stocktake_candidates(
    salon_id: int,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_salon_access(db, current_user, salon_id)
    # Stocktake candidate list should cover whole salon product dictionary
    # (same scope as "Farby i kolory"), not only products that already have stock levels.
    query = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.is_active.is_(True))
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (
                func.coalesce(LegacyProductCatalogItem.legacy_code, "").ilike(like)
                | func.coalesce(LegacyProductCatalogItem.name, "").ilike(like)
                | func.coalesce(LegacyProductCatalogItem.family_code, "").ilike(like)
            )
        )
    products = query.order_by(LegacyProductCatalogItem.name.asc()).all()

    seen: set[int] = set()
    out: list[StocktakeCandidateRead] = []
    for product in products:
        if product.id in seen:
            continue
        seen.add(product.id)
        mode = _measurement_mode_for_product(product)
        out.append(
            StocktakeCandidateRead(
                product_id=product.id,
                product_code=product.legacy_code,
                product_name=product.name,
                unit="PCS" if mode == "PCS" else "DOSE",
                measurement_mode=mode,
                dose_weight=float(_effective_dose_weight(product)) if _effective_dose_weight(product) > Decimal("0") else None,
                package_weight=float(product.package_weight) if product.package_weight is not None else None,
                full_weight=float(product.weight) if product.weight is not None else None,
            )
        )
    return out


@router.get("/issues", response_model=list[InventoryIssueRead])
async def list_inventory_issues(
    salon_id: int | None = None,
    appointment_id: int | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = db.query(InventoryIssue).filter(InventoryIssue.tenant_id == current_user.tenant_id)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(InventoryIssue.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(InventoryIssue.salon_id.in_(allowed))
    if appointment_id is not None:
        query = query.filter(InventoryIssue.appointment_id == appointment_id)
    if status_filter:
        query = query.filter(InventoryIssue.status == status_filter.upper())
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            return []
        query = query.filter(InventoryIssue.staff_id == current_staff.id)

    issues = query.order_by(InventoryIssue.issue_time.desc()).limit(300).all()
    issue_ids = [row.id for row in issues]
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, issue_ids)
    return [_issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id) for issue in issues]


@router.get("/issues/{issue_id}", response_model=InventoryIssueRead)
async def get_inventory_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    issue = _get_issue_or_404(db, issue_id, current_user.tenant_id)
    require_salon_access(db, current_user, issue.salon_id)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None or issue.staff_id != current_staff.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee can view only own issue")
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.post("/stock-adjustments/delta", response_model=InventoryIssueRead, status_code=status.HTTP_201_CREATED)
async def create_stock_adjustment_delta(
    payload: StockAdjustmentDeltaCreate,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/manager can create manual delta adjustments")
    resolved_staff_id = _ensure_inventory_write_access(db, current_user, current_staff, payload.salon_id, payload.staff_id)
    location = _resolve_salon_stock_location(db, current_user.tenant_id, payload.salon_id, payload.stock_location_id)

    issue = InventoryIssue(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        stock_location_id=location.id,
        appointment_id=None,
        service_id=None,
        performed_line_id=None,
        staff_id=resolved_staff_id,
        issue_time=payload.issue_time or datetime.utcnow(),
        status="PLANNED",
        remarks=(payload.remarks or "").strip() or "Ręczna korekta stanów (delta)",
    )
    db.add(issue)
    db.flush()

    touched_products: set[int] = set()
    created_lines = 0
    for item in payload.lines:
        delta = Decimal(str(item.delta_quantity))
        if delta == Decimal("0"):
            continue
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item.product_id}")
        level = _get_or_create_stock_level(db, location.id, item.product_id)
        current_quantity = Decimal(str(level.quantity or 0))
        unit_cost = Decimal(str(item.unit_cost)) if item.unit_cost is not None else _estimate_unit_cost(product)
        db.add(
            InventoryIssueLine(
                inventory_issue_id=issue.id,
                appointment_id=None,
                service_id=None,
                performed_line_id=None,
                product_id=item.product_id,
                quantity_planned=current_quantity,
                quantity_actual=delta,
                unit=item.unit.strip().upper(),
                unit_cost=unit_cost,
                total_cost=delta * unit_cost,
            )
        )
        touched_products.add(item.product_id)
        created_lines += 1

    if created_lines == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No non-zero adjustments provided")

    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.post("/stock-adjustments/stocktake", response_model=InventoryIssueRead, status_code=status.HTTP_201_CREATED)
async def create_stock_adjustment_stocktake(
    payload: StockAdjustmentStocktakeCreate,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    resolved_staff_id = _ensure_inventory_write_access(db, current_user, current_staff, payload.salon_id, payload.staff_id)
    location = _resolve_salon_stock_location(db, current_user.tenant_id, payload.salon_id, payload.stock_location_id)

    issue = InventoryIssue(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        stock_location_id=location.id,
        appointment_id=None,
        service_id=None,
        performed_line_id=None,
        staff_id=resolved_staff_id,
        issue_time=payload.issue_time or datetime.utcnow(),
        status="PLANNED",
        remarks=(payload.remarks or "").strip() or "Remanent - policzone (oczekuje na zatwierdzenie)",
    )
    db.add(issue)
    db.flush()

    touched_products: set[int] = set()
    created_lines = 0
    for item in payload.lines:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item.product_id}")
        mode = _measurement_mode_for_product(product)
        counted_value = item.counted_quantity
        counted: Decimal
        if counted_value is None:
            if item.counted_units is not None:
                counted_value = item.counted_units
                counted = Decimal(str(counted_value))
            elif item.measured_gross_weight is not None:
                gross = Decimal(str(item.measured_gross_weight))
                tare = Decimal(str(product.package_weight or 0))
                dose_weight = _effective_dose_weight(product)
                if mode != "WEIGHT" or dose_weight <= Decimal("0"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {product.legacy_code} - {product.name} does not support weight-based stocktake",
                    )
                net_weight = gross - tare
                if net_weight < Decimal("0"):
                    net_weight = Decimal("0")
                counted = net_weight / dose_weight
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing counted value for product {product.legacy_code} - {product.name}",
                )
        else:
            counted = Decimal(str(counted_value))

        level = _get_or_create_stock_level(db, location.id, item.product_id)
        current_quantity = Decimal(str(level.quantity or 0))
        delta = counted - current_quantity
        if delta == Decimal("0"):
            continue
        unit_cost = Decimal(str(item.unit_cost)) if item.unit_cost is not None else _estimate_unit_cost(product)
        db.add(
            InventoryIssueLine(
                inventory_issue_id=issue.id,
                appointment_id=None,
                service_id=None,
                performed_line_id=None,
                product_id=item.product_id,
                quantity_planned=current_quantity,
                quantity_actual=delta,
                unit=("PCS" if mode == "PCS" else "DOSE"),
                unit_cost=unit_cost,
                total_cost=delta * unit_cost,
            )
        )
        touched_products.add(item.product_id)
        created_lines += 1

    if created_lines == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No stock changes detected in stocktake")

    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.post("/issues", response_model=InventoryIssueRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_issue(
    payload: InventoryIssueCreate,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    resolved_staff_id = _ensure_inventory_write_access(db, current_user, current_staff, payload.salon_id, payload.staff_id)
    location = _resolve_salon_stock_location(db, current_user.tenant_id, payload.salon_id, payload.stock_location_id)

    appointment_id = payload.appointment_id
    service_id = payload.service_id
    performed_line_id = payload.performed_line_id

    if appointment_id is not None:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        ).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if appointment.salon_id != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment does not belong to salon")

    if service_id is not None and not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    if performed_line_id is not None:
        performed_line = db.query(AppointmentPerformedLine).join(
            Appointment,
            Appointment.id == AppointmentPerformedLine.appointment_id,
        ).filter(
            AppointmentPerformedLine.id == performed_line_id,
            Appointment.tenant_id == current_user.tenant_id,
        ).first()
        if not performed_line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performed line not found")
        if appointment_id is not None and performed_line.appointment_id != appointment_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="performed_line_id does not match appointment_id")
        if service_id is not None and performed_line.service_id != service_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="performed_line_id does not match service_id")
        appointment_id = performed_line.appointment_id
        service_id = performed_line.service_id

    if resolved_staff_id is not None and not db.query(StaffMember.id).filter(
        StaffMember.id == resolved_staff_id,
        StaffMember.tenant_id == current_user.tenant_id,
    ).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    issue = InventoryIssue(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        stock_location_id=location.id,
        appointment_id=appointment_id,
        service_id=service_id,
        performed_line_id=performed_line_id,
        staff_id=resolved_staff_id,
        issue_time=payload.issue_time,
        status="PLANNED",
        remarks=(payload.remarks or "").strip() or None,
    )
    db.add(issue)
    db.flush()

    for item in payload.lines:
        product = None
        if item.product_id is not None:
            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item.product_id}")
        unit_cost = _decimal_or_none(item.unit_cost)
        if unit_cost is None:
            unit_cost = _estimate_unit_cost(product)
        quantity_actual = _decimal_or_none(item.quantity_actual)
        quantity_planned = _decimal_or_none(item.quantity_planned)
        total_cost = (quantity_actual or Decimal("0")) * unit_cost
        db.add(
            InventoryIssueLine(
                inventory_issue_id=issue.id,
                appointment_id=appointment_id,
                service_id=service_id,
                performed_line_id=performed_line_id,
                product_id=item.product_id,
                quantity_planned=quantity_planned,
                quantity_actual=quantity_actual,
                unit=item.unit.strip().upper(),
                unit_cost=unit_cost,
                total_cost=total_cost,
            )
        )

    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.patch("/issues/{issue_id}", response_model=InventoryIssueRead)
async def update_inventory_issue(
    issue_id: int,
    payload: InventoryIssueUpdate,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    issue = _get_issue_or_404(db, issue_id, current_user.tenant_id)
    _ensure_inventory_write_access(db, current_user, current_staff, issue.salon_id, issue.staff_id)
    if current_user.role == UserRole.EMPLOYEE and (current_staff is None or issue.staff_id != current_staff.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee can update only own issue")
    if (issue.status or "").upper() != "PLANNED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only PLANNED issue can be updated")

    lines_by_id = {
        row.id: row
        for row in db.query(InventoryIssueLine).filter(InventoryIssueLine.inventory_issue_id == issue.id).all()
    }
    if not lines_by_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issue has no lines")

    issue.remarks = (payload.remarks or "").strip() or None

    for item in payload.lines:
        line = lines_by_id.get(item.id)
        if not line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue line not found: {item.id}")
        if item.product_id is not None:
            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item.product_id}")
            line.product_id = item.product_id
            if item.unit_cost is None and Decimal(str(line.unit_cost or 0)) == Decimal("0"):
                line.unit_cost = _estimate_unit_cost(product)
        if item.quantity_actual is not None:
            line.quantity_actual = _decimal_or_none(item.quantity_actual)
        if item.unit is not None:
            line.unit = item.unit.strip().upper()
        if item.unit_cost is not None:
            line.unit_cost = Decimal(str(item.unit_cost))
        actual = Decimal(str(line.quantity_actual)) if line.quantity_actual is not None else Decimal("0")
        unit_cost = Decimal(str(line.unit_cost or 0))
        line.total_cost = actual * unit_cost

    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.post("/issues/{issue_id}/post", response_model=InventoryIssueRead)
async def post_inventory_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    issue = _get_issue_or_404(db, issue_id, current_user.tenant_id)

    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/manager can post inventory issue")
    _ensure_inventory_write_access(db, current_user, current_staff, issue.salon_id, issue.staff_id)
    if (issue.status or "").upper() != "PLANNED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only PLANNED issue can be posted")

    lines = db.query(InventoryIssueLine).filter(InventoryIssueLine.inventory_issue_id == issue.id).all()
    if not lines:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issue has no lines")

    is_adjustment_issue = (
        issue.appointment_id is None
        and issue.service_id is None
        and issue.performed_line_id is None
    )

    for line in lines:
        if line.product_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All issue lines must have product selected before posting")
        if line.quantity_actual is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All issue lines must have quantity_actual before posting")
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == line.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {line.product_id}")
        level = (
            db.query(StockLevel)
            .filter(
                StockLevel.stock_location_id == issue.stock_location_id,
                StockLevel.product_id == line.product_id,
            )
            .first()
        )
        if not level:
            level = StockLevel(
                stock_location_id=issue.stock_location_id,
                product_id=line.product_id,
                quantity=Decimal("0"),
            )
            db.add(level)
            db.flush()
        current_quantity = Decimal(str(level.quantity or 0))
        requested_quantity = Decimal(str(line.quantity_actual))
        if is_adjustment_issue:
            if requested_quantity == Decimal("0"):
                continue
            next_quantity = current_quantity + requested_quantity
        else:
            if requested_quantity <= Decimal("0"):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All issue lines must have quantity_actual > 0 before posting")
            next_quantity = current_quantity - requested_quantity
        if next_quantity < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient stock for product {product.legacy_code} - {product.name}. "
                    f"Available: {_format_qty(current_quantity)}, requested: {_format_qty(requested_quantity)}"
                ),
            )
        level.quantity = next_quantity
        line.total_cost = Decimal(str(line.quantity_actual)) * Decimal(str(line.unit_cost or 0))

    touched_products = {line.product_id for line in lines if line.product_id is not None}
    _recompute_replenishment_for_salon(db, issue.salon_id, only_product_ids=touched_products)

    issue.status = "POSTED"
    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)


@router.post("/replenishment/generate", response_model=list[ReplenishmentSuggestionRead])
async def generate_replenishment_suggestions(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    require_salon_access(db, current_user, salon_id)
    generated = _recompute_replenishment_for_salon(db, salon_id)
    db.commit()
    product_ids = {row.product_id for row in generated}
    products = {}
    if product_ids:
        products = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
        }
    return sorted(
        [_replenishment_to_read(row, products) for row in generated],
        key=lambda item: item.suggested_quantity,
        reverse=True,
    )


@router.get("/replenishment/suggestions", response_model=list[ReplenishmentSuggestionRead])
async def list_replenishment_suggestions(
    salon_id: int,
    status_filter: str = "OPEN",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_salon_access(db, current_user, salon_id)
    query = db.query(ReplenishmentSuggestion).filter(ReplenishmentSuggestion.salon_id == salon_id)
    if status_filter:
        query = query.filter(ReplenishmentSuggestion.status == status_filter.upper())
    rows = query.order_by(ReplenishmentSuggestion.generated_at.desc()).limit(500).all()
    product_ids = {row.product_id for row in rows}
    products = {}
    if product_ids:
        products = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
        }
    return [_replenishment_to_read(row, products) for row in rows]


def _purchase_order_to_read(
    row: PurchaseOrder,
    lines: list[PurchaseOrderLine],
    products: dict[int, LegacyProductCatalogItem],
) -> PurchaseOrderRead:
    return PurchaseOrderRead(
        id=row.id,
        tenant_id=row.tenant_id,
        salon_id=row.salon_id,
        created_by_user_id=row.created_by_user_id,
        approved_by_user_id=row.approved_by_user_id,
        status=row.status,
        note=row.note,
        created_at=row.created_at,
        approved_at=row.approved_at,
        ordered_at=row.ordered_at,
        lines=[
            PurchaseOrderLineRead(
                id=line.id,
                product_id=line.product_id,
                product_name=products.get(line.product_id).name if line.product_id in products else None,
                target_quantity=float(line.target_quantity) if line.target_quantity is not None else None,
                actual_quantity=float(line.actual_quantity) if line.actual_quantity is not None else None,
                ordered_quantity=float(line.ordered_quantity or 0),
                unit=line.unit,
                unit_cost=float(line.unit_cost) if line.unit_cost is not None else None,
                total_cost=float(line.total_cost) if line.total_cost is not None else None,
            )
            for line in lines
        ],
    )


def _goods_receipt_to_read(
    row: GoodsReceipt,
    lines: list[GoodsReceiptLine],
    products: dict[int, LegacyProductCatalogItem],
) -> GoodsReceiptRead:
    return GoodsReceiptRead(
        id=row.id,
        tenant_id=row.tenant_id,
        salon_id=row.salon_id,
        purchase_order_id=row.purchase_order_id,
        received_by_user_id=row.received_by_user_id,
        status=row.status,
        note=row.note,
        created_at=row.created_at,
        received_at=row.received_at,
        posted_at=row.posted_at,
        lines=[
            GoodsReceiptLineRead(
                id=line.id,
                product_id=line.product_id,
                product_name=products.get(line.product_id).name if line.product_id in products else None,
                quantity=float(line.quantity or 0),
                unit=line.unit,
                unit_cost=float(line.unit_cost) if line.unit_cost is not None else None,
                total_cost=float(line.total_cost) if line.total_cost is not None else None,
            )
            for line in lines
        ],
    )


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    require_salon_access(db, current_user, payload.salon_id)
    po = PurchaseOrder(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        created_by_user_id=current_user.id,
        status="DRAFT",
        note=(payload.note or "").strip() or None,
    )
    db.add(po)
    db.flush()

    for line in payload.lines:
        unit_cost = _decimal_or_none(line.unit_cost)
        qty = Decimal(str(line.ordered_quantity))
        db.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=line.product_id,
                target_quantity=_decimal_or_none(line.target_quantity),
                actual_quantity=_decimal_or_none(line.actual_quantity),
                ordered_quantity=qty,
                unit=(line.unit or "PCS").strip().upper(),
                unit_cost=unit_cost,
                total_cost=(qty * unit_cost) if unit_cost is not None else None,
            )
        )
    db.commit()
    db.refresh(po)
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
    product_ids = {line.product_id for line in lines}
    products = {
        row.id: row
        for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return _purchase_order_to_read(po, lines, products)


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
async def list_purchase_orders(
    salon_id: int | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == current_user.tenant_id)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(PurchaseOrder.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(PurchaseOrder.salon_id.in_(allowed))
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter.upper())
    rows = query.order_by(PurchaseOrder.created_at.desc()).limit(400).all()
    po_ids = [row.id for row in rows]
    all_lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id.in_(po_ids)).all() if po_ids else []
    lines_by_po: dict[int, list[PurchaseOrderLine]] = {}
    product_ids: set[int] = set()
    for line in all_lines:
        lines_by_po.setdefault(line.purchase_order_id, []).append(line)
        product_ids.add(line.product_id)
    products = {
        row.id: row
        for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return [_purchase_order_to_read(row, lines_by_po.get(row.id, []), products) for row in rows]


@router.post("/purchase-orders/{purchase_order_id}/approve", response_model=PurchaseOrderRead)
async def approve_purchase_order(
    purchase_order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    row = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == purchase_order_id,
        PurchaseOrder.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    require_salon_access(db, current_user, row.salon_id)
    if row.status != "DRAFT":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT purchase order can be approved")
    row.status = "APPROVED"
    row.approved_by_user_id = current_user.id
    row.approved_at = datetime.utcnow()
    db.commit()
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == row.id).all()
    product_ids = {line.product_id for line in lines}
    products = {
        p.id: p for p in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return _purchase_order_to_read(row, lines, products)


@router.post("/purchase-orders/{purchase_order_id}/order", response_model=PurchaseOrderRead)
async def mark_purchase_order_ordered(
    purchase_order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    row = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == purchase_order_id,
        PurchaseOrder.tenant_id == current_user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    require_salon_access(db, current_user, row.salon_id)
    if row.status not in {"APPROVED", "DRAFT"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only APPROVED/DRAFT purchase order can be ordered")
    row.status = "ORDERED"
    row.ordered_at = datetime.utcnow()
    if row.approved_at is None:
        row.approved_at = datetime.utcnow()
        row.approved_by_user_id = current_user.id
    db.commit()
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == row.id).all()
    product_ids = {line.product_id for line in lines}
    products = {
        p.id: p for p in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return _purchase_order_to_read(row, lines, products)


@router.post("/goods-receipts", response_model=GoodsReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_goods_receipt(
    payload: GoodsReceiptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    require_salon_access(db, current_user, payload.salon_id)

    po: PurchaseOrder | None = None
    if payload.purchase_order_id is not None:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == payload.purchase_order_id,
            PurchaseOrder.tenant_id == current_user.tenant_id,
        ).first()
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        if po.salon_id != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Purchase order does not belong to salon")

    receipt = GoodsReceipt(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        purchase_order_id=payload.purchase_order_id,
        received_by_user_id=current_user.id,
        status="DRAFT",
        note=(payload.note or "").strip() or None,
        received_at=payload.received_at or datetime.utcnow(),
    )
    db.add(receipt)
    db.flush()

    source_lines = payload.lines
    if not source_lines and po is not None:
        po_lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
        source_lines = []
        for po_line in po_lines:
            qty = Decimal(str(po_line.ordered_quantity or 0))
            if qty <= Decimal("0"):
                continue
            source_lines.append(
                {
                    "product_id": po_line.product_id,
                    "quantity": float(qty),
                    "unit": po_line.unit or "PCS",
                    "unit_cost": float(po_line.unit_cost) if po_line.unit_cost is not None else None,
                }
            )

    if not source_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goods receipt requires at least one line")

    for line in source_lines:
        if isinstance(line, dict):
            product_id = line["product_id"]
            quantity_value = line["quantity"]
            unit_value = line.get("unit", "PCS")
            unit_cost_value = line.get("unit_cost")
        else:
            product_id = line.product_id
            quantity_value = line.quantity
            unit_value = line.unit
            unit_cost_value = line.unit_cost
        qty = Decimal(str(quantity_value))
        unit_cost = _decimal_or_none(unit_cost_value)
        db.add(
            GoodsReceiptLine(
                goods_receipt_id=receipt.id,
                product_id=product_id,
                quantity=qty,
                unit=(unit_value or "PCS").strip().upper(),
                unit_cost=unit_cost,
                total_cost=(qty * unit_cost) if unit_cost is not None else None,
            )
        )

    db.commit()
    lines = db.query(GoodsReceiptLine).filter(GoodsReceiptLine.goods_receipt_id == receipt.id).all()
    product_ids = {line.product_id for line in lines}
    products = {
        p.id: p for p in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return _goods_receipt_to_read(receipt, lines, products)


@router.get("/reports/daily-outflow", response_model=list[InventoryDailyOutflowSummaryRead])
async def inventory_daily_outflow_summary(
    salon_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user) or current_user.role == UserRole.RECEPTIONIST):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    require_salon_access(db, current_user, salon_id)

    q = (
        db.query(
            func.date_trunc("day", InventoryIssue.issue_time).label("day"),
            InventoryIssue.salon_id.label("salon_id"),
            func.count(func.distinct(InventoryIssue.id)).label("posted_issue_count"),
            func.count(InventoryIssueLine.id).label("posted_line_count"),
            func.coalesce(func.sum(InventoryIssueLine.quantity_actual), 0).label("total_quantity"),
            func.coalesce(func.sum(InventoryIssueLine.total_cost), 0).label("total_material_cost"),
        )
        .join(InventoryIssueLine, InventoryIssueLine.inventory_issue_id == InventoryIssue.id)
        .filter(
            InventoryIssue.tenant_id == current_user.tenant_id,
            InventoryIssue.salon_id == salon_id,
            InventoryIssue.status == "POSTED",
        )
    )
    if date_from is not None:
        q = q.filter(InventoryIssue.issue_time >= date_from)
    if date_to is not None:
        q = q.filter(InventoryIssue.issue_time <= date_to)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            return []
        q = q.filter(InventoryIssue.staff_id == current_staff.id)

    rows = (
        q.group_by(func.date_trunc("day", InventoryIssue.issue_time), InventoryIssue.salon_id)
        .order_by(func.date_trunc("day", InventoryIssue.issue_time).desc())
        .limit(60)
        .all()
    )
    return [
        InventoryDailyOutflowSummaryRead(
            day=row.day,
            salon_id=row.salon_id,
            posted_issue_count=int(row.posted_issue_count or 0),
            posted_line_count=int(row.posted_line_count or 0),
            total_quantity=float(row.total_quantity or 0),
            total_material_cost=float(row.total_material_cost or 0),
        )
        for row in rows
    ]


@router.get("/goods-receipts", response_model=list[GoodsReceiptRead])
async def list_goods_receipts(
    salon_id: int | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = db.query(GoodsReceipt).filter(GoodsReceipt.tenant_id == current_user.tenant_id)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(GoodsReceipt.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(GoodsReceipt.salon_id.in_(allowed))
    if status_filter:
        query = query.filter(GoodsReceipt.status == status_filter.upper())
    rows = query.order_by(GoodsReceipt.created_at.desc()).limit(400).all()
    receipt_ids = [row.id for row in rows]
    all_lines = db.query(GoodsReceiptLine).filter(GoodsReceiptLine.goods_receipt_id.in_(receipt_ids)).all() if receipt_ids else []
    lines_by_receipt: dict[int, list[GoodsReceiptLine]] = {}
    product_ids: set[int] = set()
    for line in all_lines:
        lines_by_receipt.setdefault(line.goods_receipt_id, []).append(line)
        product_ids.add(line.product_id)
    products = {
        row.id: row
        for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return [_goods_receipt_to_read(row, lines_by_receipt.get(row.id, []), products) for row in rows]


@router.post("/goods-receipts/{goods_receipt_id}/post", response_model=GoodsReceiptRead)
async def post_goods_receipt(
    goods_receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (current_user.role == UserRole.ADMIN or _is_manager_role(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    receipt = db.query(GoodsReceipt).filter(
        GoodsReceipt.id == goods_receipt_id,
        GoodsReceipt.tenant_id == current_user.tenant_id,
    ).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")
    require_salon_access(db, current_user, receipt.salon_id)
    if receipt.status != "DRAFT":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT goods receipt can be posted")

    location = _resolve_salon_stock_location(db, current_user.tenant_id, receipt.salon_id, None)
    lines = db.query(GoodsReceiptLine).filter(GoodsReceiptLine.goods_receipt_id == receipt.id).all()
    if not lines:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goods receipt has no lines")

    for line in lines:
        qty = Decimal(str(line.quantity or 0))
        if qty <= Decimal("0"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All receipt lines must have quantity > 0")
        level = _get_or_create_stock_level(db, location.id, line.product_id)
        level.quantity = Decimal(str(level.quantity or 0)) + qty
        if line.unit_cost is not None:
            line.total_cost = Decimal(str(line.unit_cost or 0)) * qty

    receipt.status = "POSTED"
    receipt.posted_at = datetime.utcnow()
    receipt.received_by_user_id = current_user.id

    if receipt.purchase_order_id is not None:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == receipt.purchase_order_id).first()
        if po is not None and po.status in {"ORDERED", "APPROVED", "DRAFT"}:
            po.status = "RECEIVED"

    touched_products = {line.product_id for line in lines}
    _recompute_replenishment_for_salon(db, receipt.salon_id, only_product_ids=touched_products)

    db.commit()
    product_ids = {line.product_id for line in lines}
    products = {
        p.id: p for p in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
    } if product_ids else {}
    return _goods_receipt_to_read(receipt, lines, products)
