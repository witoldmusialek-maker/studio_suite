"""Transitional Legacy CAISSE cashier API."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    BundleCatalog,
    BundleCatalogItem,
    CashierCashSession,
    CashierExpense,
    Customer,
    LegacyProductCatalogItem,
    Payment,
    PaymentAllocation,
    PaymentLine,
    Sale,
    SaleLine,
    SalonProductCatalogItem,
    SalonServiceCatalogItem,
    ServiceCatalogItem,
    ServicePriceHistory,
    StaffMember,
    StaffPresenceEntry,
    StaffRole,
    StaffSalonMembership,
)
from app.models.user import User, UserRole
from app.schemas.legacy_caisse import (
    LegacyCaisseBundleItemRow,
    LegacyCaisseBundleRow,
    LegacyCaisseCashSessionRead,
    LegacyCaisseCashSessionWrite,
    LegacyCaisseContextResponse,
    LegacyCaisseExpenseRead,
    LegacyCaisseExpenseWrite,
    LegacyCaisseFicheCreate,
    LegacyCaisseFicheRead,
    LegacyCaisseLineRead,
    LegacyCaissePresenceRead,
    LegacyCaissePresenceWrite,
    LegacyCaisseProductRow,
    LegacyCaisseServiceRow,
    LegacyCaisseStaffRow,
    LegacyCaisseVoidResponse,
)
from app.services.legacy_catalog_service import get_legacy_catalog

router = APIRouter(prefix="/legacy/caisse", tags=["legacy-caisse"])

TWOPLACES = Decimal("0.01")
PAYMENT_METHODS = ["cash", "card", "voucher", "invitation", "credit", "attente", "mixed"]


def _money(value: Decimal | float | int | str | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _today() -> date:
    return date.today()


def _ensure_access(db: Session, current_user: User, salon_id: int) -> None:
    require_salon_access(db, current_user, salon_id)
    if current_user.role in {
        UserRole.ADMIN,
        UserRole.MANAGER,
        UserRole.MANAGER_MAIN,
        UserRole.MANAGER_SALON,
        UserRole.RECEPTIONIST,
        UserRole.EMPLOYEE,
    }:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _normalize_month(value: str | None) -> tuple[int, int]:
    if not value:
        today = _today()
        return today.year, today.month
    try:
        year_s, month_s = value.split("-", 1)
        year = int(year_s)
        month = int(month_s)
        if month < 1 or month > 12:
            raise ValueError
        return year, month
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid month, expected YYYY-MM") from exc


def _current_price_by_service(db: Session, salon_id: int) -> dict[int, Decimal]:
    rows = (
        db.query(ServicePriceHistory)
        .filter((ServicePriceHistory.salon_id == salon_id) | (ServicePriceHistory.salon_id.is_(None)))
        .order_by(ServicePriceHistory.service_id.asc(), ServicePriceHistory.id.desc())
        .all()
    )
    out: dict[int, Decimal] = {}
    for row in rows:
        if row.service_id not in out:
            out[row.service_id] = _money(row.price)
    return out


def _cash_session_to_read(row: CashierCashSession | None, salon_id: int, business_date: date) -> LegacyCaisseCashSessionRead | None:
    if not row:
        return None
    return LegacyCaisseCashSessionRead(
        id=row.id,
        salon_id=salon_id,
        business_date=business_date,
        opening_cash=float(row.opening_cash or 0),
        closing_cash=float(row.closing_cash) if row.closing_cash is not None else None,
        status=row.status,
    )


def _load_cash_session(db: Session, tenant_id: int, salon_id: int, business_date: date) -> CashierCashSession | None:
    return (
        db.query(CashierCashSession)
        .filter(
            CashierCashSession.tenant_id == tenant_id,
            CashierCashSession.salon_id == salon_id,
            CashierCashSession.business_date == business_date,
        )
        .first()
    )


def _staff_has_salon_access(db: Session, staff: StaffMember, salon_id: int) -> bool:
    if staff.salon_id == salon_id:
        return True
    return bool(
        db.query(StaffSalonMembership.id)
        .filter(
            StaffSalonMembership.staff_id == staff.id,
            StaffSalonMembership.salon_id == salon_id,
            StaffSalonMembership.is_active.is_(True),
        )
        .first()
    )


def _validate_fiche_line(db: Session, tenant_id: int, salon_id: int, item) -> StaffMember:
    staff = db.query(StaffMember).filter(StaffMember.id == item.staff_id, StaffMember.tenant_id == tenant_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Staff not found: {item.staff_id}")
    if not _staff_has_salon_access(db, staff, salon_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff does not belong to salon")

    line_kind = (item.line_kind or "service").strip().lower()
    if line_kind not in {"service", "product", "bundle"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid line_kind")
    if line_kind == "service":
        if item.service_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="service_id is required")
        service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == item.service_id, ServiceCatalogItem.is_active.is_(True)).first()
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found or inactive")
    if line_kind == "product":
        if item.product_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="product_id is required")
        product_link = (
            db.query(SalonProductCatalogItem.id)
            .filter(
                SalonProductCatalogItem.salon_id == salon_id,
                SalonProductCatalogItem.product_id == item.product_id,
                SalonProductCatalogItem.is_active.is_(True),
            )
            .first()
        )
        if not product_link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not available for salon")
    if line_kind == "bundle":
        if item.bundle_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="bundle_id is required")
        bundle = db.query(BundleCatalog).filter(BundleCatalog.id == item.bundle_id, BundleCatalog.is_active.is_(True)).first()
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found or inactive")
    return staff


def _sale_to_read(db: Session, sale: Sale) -> LegacyCaisseFicheRead:
    lines = db.query(SaleLine).filter(SaleLine.sale_id == sale.id).order_by(SaleLine.id.asc()).all()
    payment = db.query(Payment).filter(Payment.sale_id == sale.id).order_by(Payment.id.desc()).first()
    service_gross = Decimal("0")
    retail_gross = Decimal("0")
    discount_total = Decimal("0")
    out_lines: list[LegacyCaisseLineRead] = []
    for line in lines:
        line_kind = line.line_kind or ("product" if line.product_id else "service")
        total = _money(line.total_price_gross)
        discount = _money(getattr(line, "discount_amount", 0))
        if line_kind == "product":
            retail_gross += total
        else:
            service_gross += total
        discount_total += discount
        out_lines.append(
            LegacyCaisseLineRead(
                id=line.id,
                line_kind=line_kind,
                staff_id=line.staff_id,
                service_id=line.service_id,
                product_id=line.product_id,
                bundle_id=line.bundle_id,
                legacy_worker_code=line.legacy_worker_code_snapshot,
                legacy_service_code=line.legacy_service_code_snapshot,
                label=line.label_snapshot or "",
                quantity=float(line.quantity or 0),
                unit_price=float(line.unit_price_gross or 0),
                discount_amount=float(discount),
                total_gross=float(total),
            )
        )
    return LegacyCaisseFicheRead(
        sale_id=sale.id,
        payment_id=payment.id if payment else None,
        salon_id=sale.salon_id,
        customer_id=sale.customer_id,
        appointment_id=sale.appointment_id,
        sale_time=sale.sale_time,
        status=sale.status,
        total_gross=float(_money(sale.total_gross)),
        service_gross=float(service_gross),
        retail_gross=float(retail_gross),
        discount_total=float(discount_total),
        payment_method=payment.method if payment else None,
        lines=out_lines,
    )


@router.get("/context", response_model=LegacyCaisseContextResponse)
async def get_context(
    salon_id: int = Query(...),
    business_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, salon_id)
    business_date = business_date or _today()

    staff_rows = (
        db.query(StaffMember, StaffRole)
        .outerjoin(StaffRole, StaffRole.id == StaffMember.role_id)
        .filter(
            StaffMember.tenant_id == current_user.tenant_id,
            StaffMember.is_active.is_(True),
            ((StaffMember.salon_id == salon_id) | (StaffMember.salon_id.is_(None))),
        )
        .order_by(StaffMember.legacy_code.asc().nullslast(), StaffMember.display_name.asc())
        .all()
    )
    staff = [
        LegacyCaisseStaffRow(
            staff_id=row.StaffMember.id,
            staff_code=(row.StaffMember.legacy_code or "").strip(),
            staff_name=row.StaffMember.display_name,
            role_name=row.StaffRole.name if row.StaffRole else None,
            is_active=bool(row.StaffMember.is_active),
        )
        for row in staff_rows
        if (row.StaffMember.legacy_code or "").strip()
    ]

    catalog = get_legacy_catalog(db, salon_id=salon_id)
    services = [
        LegacyCaisseServiceRow(
            service_id=row["service_id"],
            service_code=row["service_code"],
            service_name=row["service_name"],
            service_segment=row["service_segment"],
            price=float(row["price"]),
            duration_minutes=int(row.get("duration_minutes") or 0),
            is_product_shortcut=str(row.get("service_segment") or "").upper() == "SPRZEDAZ",
        )
        for row in catalog.get("service_prices", [])
        if row.get("is_active", True)
    ]
    bundles = [
        LegacyCaisseBundleRow(
            bundle_id=row["bundle_id"],
            bundle_code=row["bundle_code"],
            bundle_name=row["bundle_name"],
            price=float(row["price"]),
            items=[
                LegacyCaisseBundleItemRow(
                    position=item["position"],
                    service_id=item.get("service_id"),
                    service_code=item.get("service_code") or "",
                    service_name=item.get("service_name") or "",
                    price=float(item.get("override_price") or 0),
                )
                for item in row.get("items", [])
            ],
        )
        for row in catalog.get("bundles", [])
    ]

    product_links = (
        db.query(SalonProductCatalogItem, LegacyProductCatalogItem)
        .join(LegacyProductCatalogItem, LegacyProductCatalogItem.id == SalonProductCatalogItem.product_id)
        .filter(SalonProductCatalogItem.salon_id == salon_id, SalonProductCatalogItem.is_active.is_(True), LegacyProductCatalogItem.is_active.is_(True))
        .order_by(LegacyProductCatalogItem.legacy_code.asc())
        .limit(1000)
        .all()
    )
    products = [
        LegacyCaisseProductRow(
            product_id=product.id,
            product_code=product.legacy_code,
            product_name=link.local_name or product.name_pl or product.name,
            price=float(_money(product.sale_price_gross or product.salon_sale_price or product.catalog_net_price or 0)),
            fiscal_code=product.fiscal_code,
        )
        for link, product in product_links
    ]

    session = _load_cash_session(db, current_user.tenant_id, salon_id, business_date)
    return LegacyCaisseContextResponse(
        salon_id=salon_id,
        business_date=business_date,
        staff=staff,
        services=services,
        bundles=bundles,
        products=products,
        payment_methods=PAYMENT_METHODS,
        cash_session=_cash_session_to_read(session, salon_id, business_date),
    )


@router.get("/fiches", response_model=list[LegacyCaisseFicheRead])
async def list_fiches(
    salon_id: int = Query(...),
    month: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, salon_id)
    year, month_number = _normalize_month(month)
    rows = (
        db.query(Sale)
        .filter(
            Sale.tenant_id == current_user.tenant_id,
            Sale.salon_id == salon_id,
            extract("year", Sale.sale_time) == year,
            extract("month", Sale.sale_time) == month_number,
        )
        .order_by(Sale.sale_time.desc(), Sale.id.desc())
        .limit(500)
        .all()
    )
    return [_sale_to_read(db, row) for row in rows]


@router.post("/fiches", response_model=LegacyCaisseFicheRead, status_code=status.HTTP_201_CREATED)
async def create_fiche(
    payload: LegacyCaisseFicheCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, payload.salon_id)
    sale_time = payload.sale_time or datetime.utcnow()
    if payload.customer_id is not None and not db.query(Customer.id).filter(Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if payload.appointment_id is not None:
        appt = db.query(Appointment).filter(Appointment.id == payload.appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if appt.salon_id != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment does not belong to salon")

    for item in payload.lines:
        _validate_fiche_line(db, current_user.tenant_id, payload.salon_id, item)

    sale = Sale(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        customer_id=payload.customer_id,
        appointment_id=payload.appointment_id,
        cashier_user_id=current_user.id,
        sale_time=sale_time,
        total_gross=Decimal("0"),
        status=payload.status.upper(),
    )
    db.add(sale)
    db.flush()

    service_gross = Decimal("0")
    retail_gross = Decimal("0")
    discount_total = Decimal("0")
    for item in payload.lines:
        line_kind = (item.line_kind or "service").strip().lower()
        quantity = _money(item.quantity)
        unit_price = _money(item.unit_price)
        discount = _money(item.discount_amount)
        total = (quantity * unit_price - discount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        if total < Decimal("0"):
            total = Decimal("0")
        db.add(
            SaleLine(
                sale_id=sale.id,
                product_id=item.product_id,
                service_id=item.service_id,
                staff_id=item.staff_id,
                line_kind=line_kind,
                legacy_worker_code_snapshot=item.legacy_worker_code,
                legacy_service_code_snapshot=item.legacy_service_code,
                label_snapshot=item.label,
                bundle_id=item.bundle_id,
                bundle_code_snapshot=None,
                quantity=quantity,
                unit="PCS",
                unit_price_gross=unit_price,
                total_price_gross=total,
                discount_amount=discount,
            )
        )
        if line_kind == "product":
            retail_gross += total
        else:
            service_gross += total
        discount_total += discount
    total_gross = service_gross + retail_gross
    sale.total_gross = total_gross

    method = (payload.payment_method or "cash").strip().lower()
    allocations = payload.allocations or []
    if not allocations and total_gross > Decimal("0"):
        allocations = [type("Allocation", (), {"method": method, "amount": float(total_gross), "voucher_reference": None})()]
    payment = Payment(
        tenant_id=current_user.tenant_id,
        appointment_id=payload.appointment_id,
        salon_id=payload.salon_id,
        client_id=payload.customer_id,
        created_by_user_id=current_user.id,
        sale_id=sale.id,
        method=method,
        amount=total_gross,
        service_gross=service_gross,
        retail_gross=retail_gross,
        discount_total=discount_total,
        discount_reason_snapshot=payload.motivation,
        paid_at=sale_time,
        status="completed" if payload.status.upper() != "PENDING" else "pending",
    )
    db.add(payment)
    db.flush()
    for allocation in allocations:
        db.add(PaymentAllocation(payment_id=payment.id, method=allocation.method, amount=_money(allocation.amount), voucher_reference=allocation.voucher_reference))
    for item in payload.lines:
        line_kind = (item.line_kind or "service").strip().lower()
        total = (_money(item.quantity) * _money(item.unit_price) - _money(item.discount_amount)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        db.add(
            PaymentLine(
                payment_id=payment.id,
                item_kind=line_kind,
                service_id=item.service_id,
                product_id=item.product_id,
                label=item.label,
                quantity=_money(item.quantity),
                unit_price=_money(item.unit_price),
                total_gross=max(total, Decimal("0")),
            )
        )
    db.commit()
    db.refresh(sale)
    return _sale_to_read(db, sale)


@router.post("/fiches/{sale_id}/void", response_model=LegacyCaisseVoidResponse)
async def void_fiche(
    sale_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.tenant_id == current_user.tenant_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiche not found")
    _ensure_access(db, current_user, sale.salon_id)
    sale.status = "VOID"
    db.query(Payment).filter(Payment.sale_id == sale.id).update({"status": "void"})
    db.commit()
    return LegacyCaisseVoidResponse(sale_id=sale.id, status=sale.status)


@router.get("/cash-session", response_model=LegacyCaisseCashSessionRead | None)
async def get_cash_session(
    salon_id: int = Query(...),
    business_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, salon_id)
    business_date = business_date or _today()
    return _cash_session_to_read(_load_cash_session(db, current_user.tenant_id, salon_id, business_date), salon_id, business_date)


@router.post("/cash-session", response_model=LegacyCaisseCashSessionRead)
async def upsert_cash_session(
    payload: LegacyCaisseCashSessionWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, payload.salon_id)
    business_date = payload.business_date or _today()
    row = _load_cash_session(db, current_user.tenant_id, payload.salon_id, business_date)
    if not row:
        row = CashierCashSession(
            tenant_id=current_user.tenant_id,
            salon_id=payload.salon_id,
            business_date=business_date,
            opened_by_user_id=current_user.id,
        )
        db.add(row)
    row.opening_cash = _money(payload.opening_cash)
    row.closing_cash = _money(payload.closing_cash) if payload.closing_cash is not None else None
    row.status = payload.status.upper()
    if row.status == "CLOSED" and row.closed_at is None:
        row.closed_at = datetime.utcnow()
        row.closed_by_user_id = current_user.id
    db.commit()
    db.refresh(row)
    return _cash_session_to_read(row, payload.salon_id, business_date)


@router.get("/expenses", response_model=list[LegacyCaisseExpenseRead])
async def list_expenses(
    salon_id: int = Query(...),
    month: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, salon_id)
    year, month_number = _normalize_month(month)
    rows = (
        db.query(CashierExpense)
        .filter(
            CashierExpense.tenant_id == current_user.tenant_id,
            CashierExpense.salon_id == salon_id,
            extract("year", CashierExpense.expense_date) == year,
            extract("month", CashierExpense.expense_date) == month_number,
        )
        .order_by(CashierExpense.expense_date.desc(), CashierExpense.id.desc())
        .limit(500)
        .all()
    )
    return [
        LegacyCaisseExpenseRead(
            id=row.id,
            salon_id=row.salon_id,
            expense_date=row.expense_date,
            staff_id=row.staff_id,
            expense_type=row.expense_type,
            family=row.family,
            label=row.label,
            amount_gross=float(row.amount_gross or 0),
            vat_amount=float(row.vat_amount or 0),
            amount_net=float(row.amount_net or 0),
        )
        for row in rows
    ]


@router.post("/expenses", response_model=LegacyCaisseExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: LegacyCaisseExpenseWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, payload.salon_id)
    gross = _money(payload.amount_gross)
    vat = _money(payload.vat_amount)
    row = CashierExpense(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        expense_date=payload.expense_date or _today(),
        staff_id=payload.staff_id,
        created_by_user_id=current_user.id,
        expense_type=payload.expense_type,
        family=payload.family,
        label=payload.label,
        amount_gross=gross,
        vat_amount=vat,
        amount_net=max(gross - vat, Decimal("0")),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LegacyCaisseExpenseRead(
        id=row.id,
        salon_id=row.salon_id,
        expense_date=row.expense_date,
        staff_id=row.staff_id,
        expense_type=row.expense_type,
        family=row.family,
        label=row.label,
        amount_gross=float(row.amount_gross or 0),
        vat_amount=float(row.vat_amount or 0),
        amount_net=float(row.amount_net or 0),
    )


@router.get("/presence", response_model=list[LegacyCaissePresenceRead])
async def list_presence(
    salon_id: int = Query(...),
    presence_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, salon_id)
    day = presence_date or _today()
    rows = (
        db.query(StaffPresenceEntry)
        .filter(
            StaffPresenceEntry.tenant_id == current_user.tenant_id,
            StaffPresenceEntry.salon_id == salon_id,
            StaffPresenceEntry.presence_date == day,
        )
        .order_by(StaffPresenceEntry.id.asc())
        .all()
    )
    return [
        LegacyCaissePresenceRead(
            id=row.id,
            salon_id=row.salon_id,
            staff_id=row.staff_id,
            presence_date=row.presence_date,
            status=row.status,
            time_from=row.time_from.strftime("%H:%M") if row.time_from else None,
            time_to=row.time_to.strftime("%H:%M") if row.time_to else None,
        )
        for row in rows
    ]


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid time, expected HH:MM") from exc


@router.post("/presence", response_model=LegacyCaissePresenceRead, status_code=status.HTTP_201_CREATED)
async def upsert_presence(
    payload: LegacyCaissePresenceWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_access(db, current_user, payload.salon_id)
    day = payload.presence_date or _today()
    if not db.query(StaffMember.id).filter(StaffMember.id == payload.staff_id, StaffMember.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    row = (
        db.query(StaffPresenceEntry)
        .filter(
            StaffPresenceEntry.tenant_id == current_user.tenant_id,
            StaffPresenceEntry.salon_id == payload.salon_id,
            StaffPresenceEntry.staff_id == payload.staff_id,
            StaffPresenceEntry.presence_date == day,
        )
        .first()
    )
    if not row:
        row = StaffPresenceEntry(tenant_id=current_user.tenant_id, salon_id=payload.salon_id, staff_id=payload.staff_id, presence_date=day)
        db.add(row)
    row.status = payload.status.upper()
    row.time_from = _parse_time(payload.time_from)
    row.time_to = _parse_time(payload.time_to)
    db.commit()
    db.refresh(row)
    return LegacyCaissePresenceRead(
        id=row.id,
        salon_id=row.salon_id,
        staff_id=row.staff_id,
        presence_date=row.presence_date,
        status=row.status,
        time_from=row.time_from.strftime("%H:%M") if row.time_from else None,
        time_to=row.time_to.strftime("%H:%M") if row.time_to else None,
    )
