"""Sales API (MVP)."""
from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    Customer,
    LegacyProductCatalogItem,
    Sale,
    SaleLine,
    StaffMember,
    StockLevel,
    StockLocation,
)
from app.models.user import User, UserRole
from app.schemas.sales import SaleCreate, SaleLineRead, SaleRead

router = APIRouter(prefix="/sales", tags=["sales"])


def _allowed_salons_for_user(db: Session, current_user: User, current_staff: StaffMember | None) -> set[int] | None:
    if current_user.role == UserRole.ADMIN:
        return None
    allowed = get_staff_allowed_salons(db, current_staff)
    if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not allowed:
        return None
    return allowed


def _ensure_sale_write_access(db: Session, current_user: User, salon_id: int) -> None:
    require_salon_access(db, current_user, salon_id)
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON, UserRole.RECEPTIONIST}:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _sale_to_read(sale: Sale, lines: list[SaleLine]) -> SaleRead:
    return SaleRead(
        id=sale.id,
        salon_id=sale.salon_id,
        customer_id=sale.customer_id,
        appointment_id=sale.appointment_id,
        cashier_user_id=sale.cashier_user_id,
        sale_time=sale.sale_time,
        total_gross=float(sale.total_gross),
        status=sale.status,
        lines=[
            SaleLineRead(
                id=line.id,
                product_id=line.product_id,
                quantity=float(line.quantity),
                unit=line.unit,
                unit_price_gross=float(line.unit_price_gross),
                total_price_gross=float(line.total_price_gross),
                fiscal_code=line.fiscal_code,
            )
            for line in lines
        ],
    )


def _retail_location_for_salon(db: Session, tenant_id: int, salon_id: int) -> StockLocation | None:
    return (
        db.query(StockLocation)
        .filter(
            StockLocation.tenant_id == tenant_id,
            StockLocation.salon_id == salon_id,
            StockLocation.location_type == "RETAIL",
            StockLocation.is_active.is_(True),
        )
        .order_by(StockLocation.id.asc())
        .first()
    )


def _format_qty(value: Decimal) -> str:
    normalized = value.quantize(Decimal("0.0001"))
    text = format(normalized, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: SaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_sale_write_access(db, current_user, payload.salon_id)

    if payload.customer_id is not None and not db.query(Customer.id).filter(
        Customer.id == payload.customer_id,
        Customer.tenant_id == current_user.tenant_id,
    ).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if payload.appointment_id is not None:
        appointment = db.query(Appointment).filter(
            Appointment.id == payload.appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        ).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if appointment.salon_id != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment does not belong to salon")

    sale = Sale(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        customer_id=payload.customer_id,
        appointment_id=payload.appointment_id,
        cashier_user_id=current_user.id,
        sale_time=payload.sale_time,
        total_gross=Decimal("0"),
        status="OPEN",
    )
    db.add(sale)
    db.flush()

    total = Decimal("0")
    created_lines: list[SaleLine] = []
    for item in payload.lines:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item.product_id}")
        quantity = Decimal(str(item.quantity))
        unit_price = Decimal(str(item.unit_price_gross))
        total_price = quantity * unit_price
        line = SaleLine(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=quantity,
            unit=item.unit.strip().upper(),
            unit_price_gross=unit_price,
            total_price_gross=total_price,
            fiscal_code=product.fiscal_code,
        )
        db.add(line)
        created_lines.append(line)
        total += total_price

    sale.total_gross = total
    db.commit()
    db.refresh(sale)
    for line in created_lines:
        db.refresh(line)
    return _sale_to_read(sale, created_lines)


@router.post("/{sale_id}/complete", response_model=SaleRead)
async def complete_sale(
    sale_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.tenant_id == current_user.tenant_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    _ensure_sale_write_access(db, current_user, sale.salon_id)
    if (sale.status or "").upper() != "OPEN":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only OPEN sale can be completed")

    location = _retail_location_for_salon(db, current_user.tenant_id, sale.salon_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active RETAIL stock location in salon")

    lines = db.query(SaleLine).filter(SaleLine.sale_id == sale.id).all()
    if not lines:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale has no lines")

    for line in lines:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == line.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {line.product_id}")
        level = (
            db.query(StockLevel)
            .filter(
                StockLevel.stock_location_id == location.id,
                StockLevel.product_id == line.product_id,
            )
            .first()
        )
        if not level:
            level = StockLevel(
                stock_location_id=location.id,
                product_id=line.product_id,
                quantity=Decimal("0"),
            )
            db.add(level)
            db.flush()
        current_quantity = Decimal(str(level.quantity or 0))
        requested_quantity = Decimal(str(line.quantity))
        next_quantity = current_quantity - requested_quantity
        if next_quantity < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient retail stock for product {product.legacy_code} - {product.name}. "
                    f"Available: {_format_qty(current_quantity)}, requested: {_format_qty(requested_quantity)}"
                ),
            )
        level.quantity = next_quantity

    sale.status = "COMPLETED"
    db.commit()
    db.refresh(sale)
    lines = db.query(SaleLine).filter(SaleLine.sale_id == sale.id).all()
    return _sale_to_read(sale, lines)


@router.get("", response_model=list[SaleRead])
async def list_sales(
    salon_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    query = db.query(Sale).filter(Sale.tenant_id == current_user.tenant_id)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        query = query.filter(Sale.salon_id == salon_id)
    elif allowed is not None:
        if not allowed:
            return []
        query = query.filter(Sale.salon_id.in_(allowed))

    if date_from is not None:
        query = query.filter(Sale.sale_time >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.filter(Sale.sale_time <= datetime.combine(date_to, time.max))

    sales = query.order_by(Sale.sale_time.desc()).limit(500).all()
    sale_ids = [row.id for row in sales]
    lines = db.query(SaleLine).filter(SaleLine.sale_id.in_(sale_ids) if sale_ids else False).all()
    lines_by_sale: dict[int, list[SaleLine]] = {}
    for line in lines:
        lines_by_sale.setdefault(line.sale_id, []).append(line)

    return [_sale_to_read(sale, lines_by_sale.get(sale.id, [])) for sale in sales]
