"""Inventory API."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    InventoryIssue,
    InventoryIssueLine,
    LegacyProductCatalogItem,
    ServiceCatalogItem,
    ServiceRecipeItem,
    StaffMember,
    StockLevel,
    StockLocation,
)
from app.models.user import User, UserRole
from app.schemas.inventory import (
    InventoryIssueCreate,
    InventoryIssueLineRead,
    InventoryIssueRead,
    InventoryIssueUpdate,
    StockLevelRead,
    StockLocationCreate,
    StockLocationRead,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _allowed_salons_for_user(db: Session, current_user: User, current_staff: StaffMember | None) -> set[int] | None:
    if current_user.role == UserRole.ADMIN:
        return None
    allowed = get_staff_allowed_salons(db, current_staff)
    if current_user.role == UserRole.MANAGER and not allowed:
        return None
    return allowed


def _ensure_inventory_write_access(
    db: Session,
    current_user: User,
    current_staff: StaffMember | None,
    salon_id: int,
    payload_staff_id: int | None,
) -> int | None:
    require_salon_access(db, current_user, salon_id)
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST}:
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


def _estimate_unit_cost(product: LegacyProductCatalogItem | None) -> Decimal:
    if product is None:
        return Decimal("0")
    for candidate in (product.purchase_price, product.purchase_price_c, product.catalog_net_price):
        if candidate is not None:
            return Decimal(str(candidate))
    return Decimal("0")


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


def _get_issue_or_404(db: Session, issue_id: int) -> InventoryIssue:
    issue = db.query(InventoryIssue).filter(InventoryIssue.id == issue_id).first()
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
    query = db.query(StockLocation)
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
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
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
            LegacyProductCatalogItem.name.label("product_name"),
        )
        .join(StockLocation, StockLocation.id == StockLevel.stock_location_id)
        .join(LegacyProductCatalogItem, LegacyProductCatalogItem.id == StockLevel.product_id)
    )
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(StockLocation.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(StockLocation.salon_id.in_(allowed))
    if location_id is not None:
        location = db.query(StockLocation).filter(StockLocation.id == location_id).first()
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock location not found")
        require_salon_access(db, current_user, location.salon_id)
        query = query.filter(StockLevel.stock_location_id == location_id)
    if product_id is not None:
        query = query.filter(StockLevel.product_id == product_id)
    rows = query.order_by(StockLevel.stock_location_id.asc(), StockLevel.product_id.asc()).all()
    return [
        StockLevelRead(
            id=row.StockLevel.id,
            stock_location_id=row.StockLevel.stock_location_id,
            stock_location_name=row.stock_location_name,
            salon_id=row.salon_id,
            product_id=row.StockLevel.product_id,
            product_name=row.product_name,
            quantity=float(row.StockLevel.quantity),
            unit="PCS",
        )
        for row in rows
    ]


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
    query = db.query(InventoryIssue)
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
    issue = _get_issue_or_404(db, issue_id)
    require_salon_access(db, current_user, issue.salon_id)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None or issue.staff_id != current_staff.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee can view only own issue")
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

    location = db.query(StockLocation).filter(StockLocation.id == payload.stock_location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock location not found")
    if location.salon_id != payload.salon_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock location does not belong to salon")

    appointment_id = payload.appointment_id
    service_id = payload.service_id
    performed_line_id = payload.performed_line_id

    if appointment_id is not None:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if appointment.salon_id != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment does not belong to salon")

    if service_id is not None and not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    if performed_line_id is not None:
        performed_line = db.query(AppointmentPerformedLine).filter(AppointmentPerformedLine.id == performed_line_id).first()
        if not performed_line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performed line not found")
        if appointment_id is not None and performed_line.appointment_id != appointment_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="performed_line_id does not match appointment_id")
        if service_id is not None and performed_line.service_id != service_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="performed_line_id does not match service_id")
        appointment_id = performed_line.appointment_id
        service_id = performed_line.service_id

    if resolved_staff_id is not None and not db.query(StaffMember.id).filter(StaffMember.id == resolved_staff_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    issue = InventoryIssue(
        salon_id=payload.salon_id,
        stock_location_id=payload.stock_location_id,
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
    issue = _get_issue_or_404(db, issue_id)
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
    issue = _get_issue_or_404(db, issue_id)

    _ensure_inventory_write_access(db, current_user, current_staff, issue.salon_id, issue.staff_id)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None or issue.staff_id != current_staff.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee can post only own issue")
    if (issue.status or "").upper() != "PLANNED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only PLANNED issue can be posted")

    lines = db.query(InventoryIssueLine).filter(InventoryIssueLine.inventory_issue_id == issue.id).all()
    if not lines:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issue has no lines")

    for line in lines:
        if line.product_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All issue lines must have product selected before posting")
        if line.quantity_actual is None or Decimal(str(line.quantity_actual)) <= Decimal("0"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="All issue lines must have quantity_actual before posting")
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
        level.quantity = Decimal(str(level.quantity)) - Decimal(str(line.quantity_actual))
        line.total_cost = Decimal(str(line.quantity_actual)) * Decimal(str(line.unit_cost or 0))

    issue.status = "POSTED"
    db.commit()
    db.refresh(issue)
    lines_by_issue, products_by_id, recipe_by_id = _load_issue_context(db, [issue.id])
    return _issue_to_read(issue, lines_by_issue.get(issue.id, []), products_by_id, recipe_by_id)
