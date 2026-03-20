"""Payments, discounts and invoice API."""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    AppointmentService,
    BundleCatalog,
    ClientCard,
    Customer,
    Invitation,
    LegacyProductCatalogItem,
    Payment,
    PaymentAllocation,
    PaymentLine,
    Promotion,
    Sale,
    SaleLine,
    ServiceCatalogItem,
    StaffMember,
    StockLevel,
    StockLocation,
)
from app.models.user import User, UserRole
from app.schemas.payments import (
    AppointmentInvoiceItem,
    AppointmentInvoiceRead,
    PaymentAllocationRead,
    PromotionRead,
    PromotionWrite,
    ClientCardRead,
    ClientCardWrite,
    InvitationRead,
    InvitationWrite,
    PaymentLineRead,
    PaymentRead,
    PaymentWrite,
)

router = APIRouter(tags=["payments"])

TWOPLACES = Decimal("0.01")


def _money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _client_card_to_read(row: ClientCard) -> ClientCardRead:
    return ClientCardRead(
        id=row.id,
        client_id=row.client_id,
        discount_pct=float(row.discount_pct or 0),
        expiry=row.expiry,
    )


def _invitation_to_read(row: Invitation) -> InvitationRead:
    return InvitationRead(
        id=row.id,
        client_id=row.client_id,
        service_id=row.service_id,
        expiry=row.expiry,
        used_on_payment_id=row.used_on_payment_id,
    )


def _payment_to_read(payment: Payment, lines: list[PaymentLine], allocations: list[PaymentAllocation]) -> PaymentRead:
    return PaymentRead(
        id=payment.id,
        appointment_id=payment.appointment_id,
        salon_id=payment.salon_id,
        client_id=payment.client_id,
        created_by_user_id=payment.created_by_user_id,
        sale_id=payment.sale_id,
        client_card_id=payment.client_card_id,
        promotion_id=payment.promotion_id,
        method=payment.method,
        amount=float(payment.amount or 0),
        service_gross=float(payment.service_gross or 0),
        retail_gross=float(payment.retail_gross or 0),
        discount_total=float(payment.discount_total or 0),
        discount_reason_snapshot=payment.discount_reason_snapshot,
        promotion_name_snapshot=payment.promotion_name_snapshot,
        paid_at=payment.paid_at,
        status=payment.status,
        allocations=[
            PaymentAllocationRead(
                id=row.id,
                method=row.method,
                amount=float(row.amount or 0),
                voucher_reference=row.voucher_reference,
            )
            for row in allocations
        ],
        pdf_url=f"/api/v1/payments/{payment.id}/pdf",
        lines=[
            PaymentLineRead(
                id=row.id,
                item_kind=row.item_kind,
                label=row.label,
                quantity=float(row.quantity or 0),
                unit_price=float(row.unit_price or 0),
                total_gross=float(row.total_gross or 0),
                service_id=row.service_id,
                product_id=row.product_id,
                invitation_id=row.invitation_id,
            )
            for row in lines
        ],
    )


def _promotion_to_read(row: Promotion) -> PromotionRead:
    return PromotionRead(
        id=row.id,
        name=row.name,
        promotion_type=row.promotion_type,
        value=float(row.value or 0),
        salon_id=row.salon_id,
        service_id=row.service_id,
        bundle_id=row.bundle_id,
        customer_tier=row.customer_tier,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        is_active=bool(row.is_active),
    )


def _ensure_promotion_admin_access(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/manager can manage promotions")


def _normalize_promotion_type(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized not in {"fixed_discount", "percent_discount", "fixed_price", "bundle_bonus"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid promotion type")
    return normalized


def _valid_card(db: Session, client_id: int) -> ClientCard | None:
    today = date.today()
    return (
        db.query(ClientCard)
        .filter(
            ClientCard.client_id == client_id,
            ((ClientCard.expiry.is_(None)) | (ClientCard.expiry >= today)),
        )
        .first()
    )


def _valid_invitations(db: Session, client_id: int) -> list[Invitation]:
    today = date.today()
    return (
        db.query(Invitation)
        .filter(
            Invitation.client_id == client_id,
            Invitation.used_on_payment_id.is_(None),
            ((Invitation.expiry.is_(None)) | (Invitation.expiry >= today)),
        )
        .order_by(Invitation.id.asc())
        .all()
    )


def _retail_location_for_salon(db: Session, salon_id: int) -> StockLocation | None:
    return (
        db.query(StockLocation)
        .filter(
            StockLocation.salon_id == salon_id,
            StockLocation.location_type == "RETAIL",
            StockLocation.is_active.is_(True),
        )
        .order_by(StockLocation.id.asc())
        .first()
    )


def _require_payment_access(db: Session, current_user: User, salon_id: int) -> None:
    require_salon_access(db, current_user, salon_id)
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON, UserRole.RECEPTIONIST}:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _normalize_payment_method(value: str | None) -> str:
    method = (value or "").strip().lower()
    if method not in {"cash", "card", "voucher", "transfer"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid payment method")
    return method


@router.get("/payments/promotions", response_model=list[PromotionRead])
async def list_active_promotions(
    salon_id: int | None = Query(default=None),
    appointment_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if salon_id is not None:
        _require_payment_access(db, current_user, salon_id)
    elif current_user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    appointment: Appointment | None = None
    performed_service_ids: set[int] = set()
    linked_service_ids: set[int] = set()
    bundle_id: int | None = None
    if appointment_id is not None:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if salon_id is not None and appointment.salon_id != salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment does not belong to this salon")
        if salon_id is None:
            salon_id = appointment.salon_id
        performed_service_ids = {
            row[0]
            for row in db.query(AppointmentPerformedLine.service_id).filter(AppointmentPerformedLine.appointment_id == appointment.id).all()
        }
        linked_service_ids = {
            row[0]
            for row in db.query(AppointmentService.service_id).filter(AppointmentService.appointment_id == appointment.id).all()
        }
        bundle_id = appointment.bundle_id

    today = date.today()
    rows = (
        db.query(Promotion)
        .filter(
            Promotion.is_active.is_(True),
            ((Promotion.valid_from.is_(None)) | (Promotion.valid_from <= today)),
            ((Promotion.valid_to.is_(None)) | (Promotion.valid_to >= today)),
        )
        .order_by(Promotion.name.asc())
    )
    if salon_id is not None:
        rows = rows.filter((Promotion.salon_id.is_(None)) | (Promotion.salon_id == salon_id))
    rows = rows.all()
    eligible: list[Promotion] = []
    allowed_service_ids = performed_service_ids.union(linked_service_ids)
    for row in rows:
        if row.service_id is not None and row.service_id not in allowed_service_ids:
            continue
        if row.bundle_id is not None and row.bundle_id != bundle_id:
            continue
        eligible.append(row)
    return [_promotion_to_read(row) for row in eligible]


@router.post("/payments/promotions", response_model=PromotionRead, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    payload: PromotionWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_promotion_admin_access(current_user)
    if payload.salon_id is not None:
        require_salon_access(db, current_user, payload.salon_id)
    if payload.service_id is not None and not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == payload.service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if payload.bundle_id is not None and not db.query(BundleCatalog.id).filter(BundleCatalog.id == payload.bundle_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
    if payload.valid_from and payload.valid_to and payload.valid_from > payload.valid_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="valid_from cannot be after valid_to")
    row = Promotion(
        name=payload.name.strip(),
        promotion_type=_normalize_promotion_type(payload.promotion_type),
        value=_money(payload.value),
        salon_id=payload.salon_id,
        service_id=payload.service_id,
        bundle_id=payload.bundle_id,
        customer_tier=(payload.customer_tier or "").strip().upper() or None,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _promotion_to_read(row)


@router.patch("/payments/promotions/{promotion_id}", response_model=PromotionRead)
async def update_promotion(
    promotion_id: int,
    payload: PromotionWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_promotion_admin_access(current_user)
    row = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    target_salon_id = payload.salon_id if payload.salon_id is not None else row.salon_id
    if target_salon_id is not None:
        require_salon_access(db, current_user, target_salon_id)
    if payload.service_id is not None and not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == payload.service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if payload.bundle_id is not None and not db.query(BundleCatalog.id).filter(BundleCatalog.id == payload.bundle_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
    if payload.valid_from and payload.valid_to and payload.valid_from > payload.valid_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="valid_from cannot be after valid_to")
    row.name = payload.name.strip()
    row.promotion_type = _normalize_promotion_type(payload.promotion_type)
    row.value = _money(payload.value)
    row.salon_id = payload.salon_id
    row.service_id = payload.service_id
    row.bundle_id = payload.bundle_id
    row.customer_tier = (payload.customer_tier or "").strip().upper() or None
    row.valid_from = payload.valid_from
    row.valid_to = payload.valid_to
    row.is_active = payload.is_active
    db.commit()
    db.refresh(row)
    return _promotion_to_read(row)


@router.delete("/payments/promotions/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promotion(
    promotion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_promotion_admin_access(current_user)
    row = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    if row.salon_id is not None:
        require_salon_access(db, current_user, row.salon_id)
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _collect_invoice_items(db: Session, appointment: Appointment) -> list[dict]:
    performed = (
        db.query(AppointmentPerformedLine, ServiceCatalogItem)
        .join(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .filter(AppointmentPerformedLine.appointment_id == appointment.id)
        .order_by(AppointmentPerformedLine.id.asc())
        .all()
    )
    if performed:
        return [
            {
                "service_id": line.service_id,
                "kind": "service",
                "label": service.name,
                "quantity": Decimal("1"),
                "unit_price": _money(line.price_snapshot or 0),
            }
            for line, service in performed
        ]

    links = (
        db.query(AppointmentService, ServiceCatalogItem)
        .join(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentService.service_id)
        .filter(AppointmentService.appointment_id == appointment.id)
        .order_by(AppointmentService.id.asc())
        .all()
    )
    items = []
    for link, service in links:
        items.append(
            {
                "service_id": link.service_id,
                "kind": "service",
                "label": service.name,
                "quantity": Decimal("1"),
                "unit_price": _money(service.default_price or 0),
            }
        )
    if not items:
        items.append(
            {
                "service_id": None,
                "kind": "service",
                "label": "Wizyta",
                "quantity": Decimal("1"),
                "unit_price": _money(appointment.total_price_snapshot or 0),
            }
        )
    return items


def _build_invoice(
    db: Session,
    appointment: Appointment,
    use_card: bool,
    invitation_ids: list[int],
    retail_items: list[dict] | None = None,
) -> tuple[dict, list[dict], ClientCard | None, list[Invitation]]:
    service_items = _collect_invoice_items(db, appointment)
    valid_card = _valid_card(db, appointment.client_id)
    available_invitations = _valid_invitations(db, appointment.client_id)
    available_by_id = {row.id: row for row in available_invitations}
    selected_invitations: list[Invitation] = []
    used_service_slots: set[int] = set()

    invitation_discount = Decimal("0")
    for invitation_id in invitation_ids:
        invitation = available_by_id.get(invitation_id)
        if not invitation:
            continue
        selected_index = next(
            (
                index
                for index, item in enumerate(service_items)
                if item["service_id"] == invitation.service_id and index not in used_service_slots
            ),
            None,
        )
        if selected_index is None:
            continue
        used_service_slots.add(selected_index)
        service_items[selected_index]["discount_value"] = service_items[selected_index]["unit_price"]
        service_items[selected_index]["invitation_id"] = invitation.id
        invitation_discount += service_items[selected_index]["unit_price"]
        selected_invitations.append(invitation)

    service_gross = sum((item["unit_price"] for item in service_items), Decimal("0"))
    service_after_invitations = service_gross - invitation_discount

    card_discount = Decimal("0")
    if use_card and valid_card and service_after_invitations > 0:
        card_discount = _money(service_after_invitations * (Decimal(str(valid_card.discount_pct)) / Decimal("100")))

    retail_rows: list[dict] = []
    retail_gross = Decimal("0")
    for item in retail_items or []:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item["product_id"]).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product not found: {item['product_id']}")
        qty = _money(item["quantity"])
        unit_price = _money(product.sale_price_gross or product.salon_sale_price or 0)
        total = _money(qty * unit_price)
        retail_rows.append(
            {
                "product_id": product.id,
                "kind": "retail",
                "label": product.name_pl or product.name,
                "quantity": qty,
                "unit_price": unit_price,
                "total_gross": total,
            }
        )
        retail_gross += total

    total_discount = invitation_discount + card_discount
    net_total = service_gross + retail_gross - total_discount

    invoice_rows = []
    for index, item in enumerate(service_items):
        discount_value = _money(item.get("discount_value", 0))
        total = item["unit_price"] - discount_value
        invoice_rows.append(
            {
                "service_id": item["service_id"],
                "product_id": None,
                "kind": item["kind"],
                "label": item["label"],
                "quantity": float(item["quantity"]),
                "unit_price": float(item["unit_price"]),
                "total_gross": float(total),
                "discount_value": float(discount_value),
                "invitation_id": item.get("invitation_id"),
            }
        )
    for retail in retail_rows:
        invoice_rows.append(
            {
                "service_id": None,
                "product_id": retail["product_id"],
                "kind": retail["kind"],
                "label": retail["label"],
                "quantity": float(retail["quantity"]),
                "unit_price": float(retail["unit_price"]),
                "total_gross": float(retail["total_gross"]),
                "discount_value": 0.0,
                "invitation_id": None,
            }
        )

    payload = {
        "appointment_id": appointment.id,
        "client_id": appointment.client_id,
        "service_gross": float(service_gross),
        "retail_gross": float(retail_gross),
        "card_discount": float(card_discount),
        "invitation_discount": float(invitation_discount),
        "total_discount": float(total_discount),
        "net_total": float(net_total),
    }
    return payload, invoice_rows, valid_card if use_card else None, available_invitations


def _render_pdf(lines: list[str]) -> bytes:
    text_lines = []
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_lines.append(f"({safe}) Tj")
    body = "BT /F1 12 Tf 40 780 Td 14 TL " + " T* ".join(text_lines) + " ET"
    stream = body.encode("latin-1", "replace")
    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n")
    objects.append(f"4 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")
    objects.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    out.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    out.write(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return out.getvalue()


@router.get("/clients/{client_id}/card", response_model=ClientCardRead | None)
async def get_client_card(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    row = db.query(ClientCard).filter(ClientCard.client_id == client_id).first()
    return _client_card_to_read(row) if row else None


@router.post("/clients/{client_id}/card", response_model=ClientCardRead)
async def upsert_client_card(
    client_id: int,
    payload: ClientCardWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    if not db.query(Customer.id).filter(Customer.id == client_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    row = db.query(ClientCard).filter(ClientCard.client_id == client_id).first()
    if not row:
        row = ClientCard(client_id=client_id)
        db.add(row)
    row.discount_pct = _money(payload.discount_pct)
    row.expiry = payload.expiry
    db.commit()
    db.refresh(row)
    return _client_card_to_read(row)


@router.get("/clients/{client_id}/invitations", response_model=list[InvitationRead])
async def list_invitations(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return [_invitation_to_read(row) for row in _valid_invitations(db, client_id)]


@router.post("/clients/{client_id}/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    client_id: int,
    payload: InvitationWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    if not db.query(Customer.id).filter(Customer.id == client_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    invitation = Invitation(client_id=client_id, service_id=payload.service_id, expiry=payload.expiry)
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return _invitation_to_read(invitation)


@router.get("/appointments/{appointment_id}/invoice", response_model=AppointmentInvoiceRead)
async def get_invoice_preview(
    appointment_id: int,
    use_card: bool = False,
    invitation_ids: list[int] = Query(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_payment_access(db, current_user, appointment.salon_id)
    totals, rows, card, invitations = _build_invoice(db, appointment, use_card, invitation_ids, [])
    return AppointmentInvoiceRead(
        **totals,
        eligible_card=_client_card_to_read(card) if card else None,
        available_invitations=[_invitation_to_read(row) for row in invitations],
        items=[AppointmentInvoiceItem(**row) for row in rows],
    )


@router.post("/payments/{appointment_id}", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    appointment_id: int,
    payload: PaymentWrite,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    del current_staff
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_payment_access(db, current_user, appointment.salon_id)

    totals, rows, card, invitations = _build_invoice(
        db,
        appointment,
        payload.use_card,
        payload.invitation_ids,
        [{"product_id": item.product_id, "quantity": item.quantity} for item in payload.retail_items],
    )

    expected_amount = _money(totals["net_total"])
    if _money(payload.amount) != expected_amount:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Amount mismatch, expected {expected_amount}")
    allocations_input = payload.allocations or []
    created_allocations: list[PaymentAllocation] = []
    if allocations_input:
        normalized_allocations = []
        total_allocated = Decimal("0")
        for allocation in allocations_input:
            method = _normalize_payment_method(allocation.method)
            amount = _money(allocation.amount)
            total_allocated += amount
            normalized_allocations.append(
                {
                    "method": method,
                    "amount": amount,
                    "voucher_reference": (allocation.voucher_reference or "").strip() or None,
                }
            )
        if total_allocated != expected_amount:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Allocation mismatch, expected {expected_amount}")
    else:
        normalized_allocations = [
            {
                "method": _normalize_payment_method(payload.method),
                "amount": expected_amount,
                "voucher_reference": None,
            }
        ]
    primary_method = normalized_allocations[0]["method"] if len(normalized_allocations) == 1 else "mixed"

    promotion: Promotion | None = None
    if payload.promotion_id is not None:
        promotion = db.query(Promotion).filter(Promotion.id == payload.promotion_id, Promotion.is_active.is_(True)).first()
        if not promotion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
        if promotion.salon_id is not None and promotion.salon_id != appointment.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promotion does not belong to this salon")
        if promotion.service_id is not None:
            performed_service_ids = {
                row[0]
                for row in db.query(AppointmentPerformedLine.service_id).filter(AppointmentPerformedLine.appointment_id == appointment.id).all()
            }
            linked_service_ids = {
                row[0]
                for row in db.query(AppointmentService.service_id).filter(AppointmentService.appointment_id == appointment.id).all()
            }
            if promotion.service_id not in performed_service_ids.union(linked_service_ids):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promotion does not match appointment services")

    sale: Sale | None = None
    sale_line_ids_by_product: dict[int, int] = {}
    retail_rows = [row for row in rows if row["kind"] == "retail"]
    if retail_rows:
        sale = Sale(
            salon_id=appointment.salon_id,
            customer_id=appointment.client_id,
            appointment_id=appointment.id,
            cashier_user_id=current_user.id,
            sale_time=datetime.now(),
            total_gross=_money(totals["retail_gross"]),
            status="COMPLETED",
        )
        db.add(sale)
        db.flush()
        location = _retail_location_for_salon(db, appointment.salon_id)
        for retail in retail_rows:
            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == retail["product_id"]).first()
            sale_line = SaleLine(
                sale_id=sale.id,
                product_id=product.id,
                quantity=_money(retail["quantity"]),
                unit="PCS",
                unit_price_gross=_money(retail["unit_price"]),
                total_price_gross=_money(retail["total_gross"]),
                fiscal_code=product.fiscal_code,
            )
            db.add(sale_line)
            db.flush()
            sale_line_ids_by_product[product.id] = sale_line.id
            if location:
                level = (
                    db.query(StockLevel)
                    .filter(StockLevel.stock_location_id == location.id, StockLevel.product_id == product.id)
                    .first()
                )
                if not level:
                    level = StockLevel(stock_location_id=location.id, product_id=product.id, quantity=Decimal("0"))
                    db.add(level)
                    db.flush()
                level.quantity = Decimal(str(level.quantity)) - _money(retail["quantity"])

    payment = Payment(
        appointment_id=appointment.id,
        salon_id=appointment.salon_id,
        client_id=appointment.client_id,
        created_by_user_id=current_user.id,
        sale_id=sale.id if sale else None,
        client_card_id=card.id if card else None,
        promotion_id=promotion.id if promotion else None,
        method=primary_method,
        amount=expected_amount,
        service_gross=_money(totals["service_gross"]),
        retail_gross=_money(totals["retail_gross"]),
        discount_total=_money(totals["total_discount"]),
        discount_reason_snapshot=(
            "client_card+invitation"
            if totals["card_discount"] > 0 and payload.invitation_ids
            else "client_card"
            if totals["card_discount"] > 0
            else "invitation"
            if payload.invitation_ids
            else None
        ),
        promotion_name_snapshot=(payload.promotion_name or "").strip() or (promotion.name if promotion else None),
        paid_at=datetime.now(),
        status="COMPLETED",
    )
    db.add(payment)
    db.flush()

    for allocation in normalized_allocations:
        payment_allocation = PaymentAllocation(
            payment_id=payment.id,
            method=allocation["method"],
            amount=allocation["amount"],
            voucher_reference=allocation["voucher_reference"],
        )
        db.add(payment_allocation)
        created_allocations.append(payment_allocation)

    invitation_map = {row.id: row for row in invitations}
    created_lines: list[PaymentLine] = []
    for row in rows:
        line = PaymentLine(
            payment_id=payment.id,
            item_kind=row["kind"],
            service_id=row["service_id"],
            product_id=row["product_id"],
            invitation_id=row.get("invitation_id"),
            label=row["label"],
            quantity=_money(row["quantity"]),
            unit_price=_money(row["unit_price"]),
            total_gross=_money(row["total_gross"]),
        )
        db.add(line)
        created_lines.append(line)

    if totals["card_discount"] > 0:
        discount_line = PaymentLine(
            payment_id=payment.id,
            item_kind="discount",
            label="Karta stalego klienta",
            quantity=Decimal("1"),
            unit_price=_money(-totals["card_discount"]),
            total_gross=_money(-totals["card_discount"]),
        )
        db.add(discount_line)
        created_lines.append(discount_line)

    for invitation_id in payload.invitation_ids:
        invitation = invitation_map.get(invitation_id)
        if invitation:
            invitation.used_on_payment_id = payment.id

    db.commit()
    db.refresh(payment)
    for allocation in created_allocations:
        db.refresh(allocation)
    for line in created_lines:
        db.refresh(line)
    return _payment_to_read(payment, created_lines, created_allocations)


@router.get("/payments/{payment_id}/pdf")
async def payment_pdf(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    _require_payment_access(db, current_user, payment.salon_id)
    lines = db.query(PaymentLine).filter(PaymentLine.payment_id == payment.id).order_by(PaymentLine.id.asc()).all()
    pdf = _render_pdf(
        [
            "Studio Suite - Rozliczenie",
            f"Payment ID: {payment.id}",
            f"Appointment: {payment.appointment_id}",
            f"Method: {payment.method}",
            f"Amount: {float(payment.amount or 0):.2f} PLN",
            *[
                f"- {row.label}: {float(row.total_gross or 0):.2f} PLN"
                for row in lines
            ],
        ]
    )
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename=\"payment-{payment.id}.pdf\"'})
