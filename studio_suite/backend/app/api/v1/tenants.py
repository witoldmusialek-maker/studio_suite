import re
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_superadmin
from app.database import get_db
from app.models.user import Tenant, TenantBillingInvoice, TenantModuleLicense, User, UserRole
from app.schemas.user import (
    TenantCreate,
    TenantBillingInvoiceLine,
    TenantBillingInvoiceResponse,
    TenantBillingMarkPaidRequest,
    TenantModuleLicensePayload,
    TenantModuleLicenseResponse,
    TenantResponse,
    TenantUpdate,
)
from app.services.billing import ensure_tenant_invoice, process_billing_reminders
from app.utils.security import get_password_hash

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _normalize_code(value: str) -> str:
    return value.strip().upper().replace(" ", "_")


def _normalize_username(value: str) -> str:
    return value.strip().lower()


def _validate_password_strength(password: str) -> None:
    issues: list[str] = []
    if len(password) < 10:
        issues.append("minimum length is 10 characters")
    if not re.search(r"[a-z]", password):
        issues.append("must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        issues.append("must contain an uppercase letter")
    if not re.search(r"\d", password):
        issues.append("must contain a digit")
    if any(ch.isspace() for ch in password):
        issues.append("cannot contain spaces")
    if issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements: " + "; ".join(issues),
        )


def _invoice_to_response(row: TenantBillingInvoice) -> TenantBillingInvoiceResponse:
    line_items: list[TenantBillingInvoiceLine] = []
    if row.line_items_json:
        try:
            payload = json.loads(row.line_items_json)
            if isinstance(payload, list):
                line_items = [
                    TenantBillingInvoiceLine(
                        code=str(item.get("code", "")),
                        label=str(item.get("label", "")),
                        amount=float(item.get("amount", 0) or 0),
                    )
                    for item in payload
                    if isinstance(item, dict)
                ]
        except json.JSONDecodeError:
            line_items = []
    return TenantBillingInvoiceResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        period_year=row.period_year,
        period_month=row.period_month,
        issue_date=row.issue_date,
        due_date=row.due_date,
        currency=row.currency,
        base_amount=float(row.base_amount or 0),
        modules_amount=float(row.modules_amount or 0),
        total_amount=float(row.total_amount or 0),
        status=row.status,
        notes=row.notes,
        sent_at=row.sent_at,
        paid_at=row.paid_at,
        line_items=line_items,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    return db.query(Tenant).order_by(Tenant.id.asc()).all()


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    code = _normalize_code(payload.code)
    if db.query(Tenant).filter(Tenant.code == code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant code already exists")
    tenant = Tenant(
        code=code,
        name=payload.name.strip(),
        is_active=bool(payload.is_active),
        billing_plan=payload.billing_plan.strip().upper(),
        billing_cycle=payload.billing_cycle.strip().lower(),
        monthly_base_price=payload.monthly_base_price,
        billing_email=(payload.billing_email or "").strip() or None,
        description=(payload.description or "").strip() or None,
        legal_name=(payload.legal_name or "").strip() or None,
        tax_id=(payload.tax_id or "").strip() or None,
        billing_address_line1=(payload.billing_address_line1 or "").strip() or None,
        billing_address_line2=(payload.billing_address_line2 or "").strip() or None,
        billing_postal_code=(payload.billing_postal_code or "").strip() or None,
        billing_city=(payload.billing_city or "").strip() or None,
        billing_country=(payload.billing_country or "PL").strip().upper() or "PL",
        billing_contact_name=(payload.billing_contact_name or "").strip() or None,
        billing_contact_phone=(payload.billing_contact_phone or "").strip() or None,
        billing_due_days=max(1, min(90, int(payload.billing_due_days or 14))),
    )
    db.add(tenant)
    db.flush()
    if payload.admin_username:
        admin_username = _normalize_username(payload.admin_username)
        if db.query(User).filter(User.username == admin_username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin username already exists")
        if not payload.admin_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin password is required")
        _validate_password_strength(payload.admin_password)
        db.add(
            User(
                tenant_id=tenant.id,
                username=admin_username,
                password_hash=get_password_hash(payload.admin_password),
                role=UserRole.ADMIN,
                is_superadmin=False,
            )
        )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if payload.code is not None:
        code = _normalize_code(payload.code)
        existing = db.query(Tenant).filter(Tenant.code == code, Tenant.id != tenant_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant code already exists")
        tenant.code = code
    if payload.name is not None:
        tenant.name = payload.name.strip()
    if payload.is_active is not None:
        tenant.is_active = bool(payload.is_active)
    if payload.billing_plan is not None:
        tenant.billing_plan = payload.billing_plan.strip().upper()
    if payload.billing_cycle is not None:
        tenant.billing_cycle = payload.billing_cycle.strip().lower()
    if payload.monthly_base_price is not None:
        tenant.monthly_base_price = payload.monthly_base_price
    if payload.billing_email is not None:
        tenant.billing_email = payload.billing_email.strip() or None
    if payload.description is not None:
        tenant.description = payload.description.strip() or None
    if payload.legal_name is not None:
        tenant.legal_name = payload.legal_name.strip() or None
    if payload.tax_id is not None:
        tenant.tax_id = payload.tax_id.strip() or None
    if payload.billing_address_line1 is not None:
        tenant.billing_address_line1 = payload.billing_address_line1.strip() or None
    if payload.billing_address_line2 is not None:
        tenant.billing_address_line2 = payload.billing_address_line2.strip() or None
    if payload.billing_postal_code is not None:
        tenant.billing_postal_code = payload.billing_postal_code.strip() or None
    if payload.billing_city is not None:
        tenant.billing_city = payload.billing_city.strip() or None
    if payload.billing_country is not None:
        tenant.billing_country = payload.billing_country.strip().upper() or "PL"
    if payload.billing_contact_name is not None:
        tenant.billing_contact_name = payload.billing_contact_name.strip() or None
    if payload.billing_contact_phone is not None:
        tenant.billing_contact_phone = payload.billing_contact_phone.strip() or None
    if payload.billing_due_days is not None:
        tenant.billing_due_days = max(1, min(90, int(payload.billing_due_days)))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if tenant.id == 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default tenant cannot be deleted")
    try:
        db.delete(tenant)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant has linked data. Deactivate it instead.",
        ) from None
    return None


@router.get("/{tenant_id}/licenses", response_model=list[TenantModuleLicenseResponse])
async def list_tenant_licenses(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return (
        db.query(TenantModuleLicense)
        .filter(TenantModuleLicense.tenant_id == tenant_id)
        .order_by(TenantModuleLicense.module_code.asc())
        .all()
    )


@router.get("/{tenant_id}/billing/invoices", response_model=list[TenantBillingInvoiceResponse])
async def list_tenant_billing_invoices(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    rows = (
        db.query(TenantBillingInvoice)
        .filter(TenantBillingInvoice.tenant_id == tenant_id)
        .order_by(TenantBillingInvoice.period_year.desc(), TenantBillingInvoice.period_month.desc())
        .limit(24)
        .all()
    )
    return [_invoice_to_response(row) for row in rows]


@router.post("/{tenant_id}/billing/generate", response_model=TenantBillingInvoiceResponse)
async def generate_tenant_billing_invoice(
    tenant_id: int,
    period_year: int | None = None,
    period_month: int | None = None,
    force_recalculate: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    now = datetime.utcnow()
    year = int(period_year or now.year)
    month = int(period_month or now.month)
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month")
    row = ensure_tenant_invoice(db, tenant_id, year, month, force_recalculate=force_recalculate)
    db.commit()
    db.refresh(row)
    return _invoice_to_response(row)


@router.post("/{tenant_id}/billing/invoices/{invoice_id}/paid", response_model=TenantBillingInvoiceResponse)
async def set_tenant_invoice_paid(
    tenant_id: int,
    invoice_id: int,
    payload: TenantBillingMarkPaidRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    row = (
        db.query(TenantBillingInvoice)
        .filter(
            TenantBillingInvoice.id == invoice_id,
            TenantBillingInvoice.tenant_id == tenant_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if payload.paid:
        row.status = "PAID"
        row.paid_at = datetime.utcnow()
    else:
        row.paid_at = None
        row.status = "OPEN"
    if payload.notes is not None:
        row.notes = payload.notes.strip() or None
    db.commit()
    db.refresh(row)
    return _invoice_to_response(row)


@router.post("/billing/reminders/run")
async def run_billing_reminders(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    result = process_billing_reminders(db)
    return {"status": "ok", **result}


@router.put("/{tenant_id}/licenses", response_model=list[TenantModuleLicenseResponse])
async def replace_tenant_licenses(
    tenant_id: int,
    payload: list[TenantModuleLicensePayload],
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    db.query(TenantModuleLicense).filter(TenantModuleLicense.tenant_id == tenant_id).delete()
    rows: list[TenantModuleLicense] = []
    for item in payload:
        rows.append(
            TenantModuleLicense(
                tenant_id=tenant_id,
                module_code=item.module_code.strip().upper(),
                is_enabled=bool(item.is_enabled),
                monthly_price=item.monthly_price,
                notes=(item.notes or "").strip() or None,
            )
        )
    if rows:
        db.add_all(rows)
    db.commit()
    return (
        db.query(TenantModuleLicense)
        .filter(TenantModuleLicense.tenant_id == tenant_id)
        .order_by(TenantModuleLicense.module_code.asc())
        .all()
    )
