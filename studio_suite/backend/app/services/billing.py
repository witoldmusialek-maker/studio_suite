from __future__ import annotations

import json
import smtplib
import ssl
import threading
import time
from datetime import date, datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.user import Tenant, TenantBillingInvoice, TenantBillingReminderLog, TenantModuleLicense

_billing_scheduler_started = False
_billing_scheduler_lock = threading.Lock()


def _parse_int_list(raw: str) -> list[int]:
    values: list[int] = []
    for chunk in (raw or "").split(","):
        item = chunk.strip()
        if not item:
            continue
        try:
            values.append(int(item))
        except ValueError:
            continue
    return sorted(set(values))


def is_smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


def send_billing_email(to_email: str, subject: str, body: str) -> None:
    if not is_smtp_configured():
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(body)

    if settings.SMTP_USE_SSL:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=20) as server:
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
            server.send_message(message)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        if settings.SMTP_USE_STARTTLS:
            server.starttls(context=ssl.create_default_context())
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        server.send_message(message)


def calculate_tenant_monthly_charges(db: Session, tenant_id: int) -> dict[str, object]:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError("tenant_not_found")
    base_amount = float(tenant.monthly_base_price or 0)
    module_rows = (
        db.query(TenantModuleLicense)
        .filter(
            TenantModuleLicense.tenant_id == tenant_id,
            TenantModuleLicense.is_enabled.is_(True),
        )
        .order_by(TenantModuleLicense.module_code.asc())
        .all()
    )
    module_lines = [
        {
            "code": row.module_code,
            "label": f"Modul {row.module_code}",
            "amount": float(row.monthly_price or 0),
        }
        for row in module_rows
    ]
    modules_amount = sum(float(row["amount"]) for row in module_lines)
    total_amount = base_amount + modules_amount
    lines = [{"code": "BASE", "label": "Abonament bazowy", "amount": base_amount}] + module_lines
    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "base_amount": round(base_amount, 2),
        "modules_amount": round(modules_amount, 2),
        "total_amount": round(total_amount, 2),
        "currency": (settings.BILLING_CURRENCY or "PLN").upper(),
        "line_items": lines,
    }


def ensure_tenant_invoice(
    db: Session,
    tenant_id: int,
    period_year: int,
    period_month: int,
    *,
    force_recalculate: bool = False,
) -> TenantBillingInvoice:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError("tenant_not_found")

    invoice = (
        db.query(TenantBillingInvoice)
        .filter(
            TenantBillingInvoice.tenant_id == tenant_id,
            TenantBillingInvoice.period_year == period_year,
            TenantBillingInvoice.period_month == period_month,
        )
        .first()
    )
    if invoice and not force_recalculate:
        return invoice

    charges = calculate_tenant_monthly_charges(db, tenant_id)
    issue_date = date(period_year, period_month, 1)
    due_days = max(1, int(tenant.billing_due_days or 14))
    due_date = issue_date + timedelta(days=due_days)
    line_items_json = json.dumps(charges["line_items"], ensure_ascii=False)

    if invoice is None:
        invoice = TenantBillingInvoice(
            tenant_id=tenant_id,
            period_year=period_year,
            period_month=period_month,
            issue_date=issue_date,
            due_date=due_date,
            currency=str(charges["currency"]),
            base_amount=float(charges["base_amount"]),
            modules_amount=float(charges["modules_amount"]),
            total_amount=float(charges["total_amount"]),
            status="OPEN",
            line_items_json=line_items_json,
        )
        db.add(invoice)
    else:
        if invoice.status != "PAID":
            invoice.base_amount = float(charges["base_amount"])
            invoice.modules_amount = float(charges["modules_amount"])
            invoice.total_amount = float(charges["total_amount"])
            invoice.currency = str(charges["currency"])
            invoice.due_date = due_date
            invoice.line_items_json = line_items_json
    db.flush()
    return invoice


def _render_invoice_message(tenant: Tenant, invoice: TenantBillingInvoice, reminder_kind: str) -> tuple[str, str]:
    period = f"{invoice.period_year}-{invoice.period_month:02d}"
    subject_prefix = "Przypomnienie platnosci"
    if reminder_kind.startswith("OVERDUE_"):
        subject_prefix = "Zaleglosc platnosci"
    subject = f"[Studio Suite] {subject_prefix} - {tenant.name} - {period}"
    body = (
        f"Tenant: {tenant.name} ({tenant.code})\n"
        f"Okres rozliczeniowy: {period}\n"
        f"Kwota: {float(invoice.total_amount):.2f} {invoice.currency}\n"
        f"Termin platnosci: {invoice.due_date.isoformat()}\n"
        f"Status: {invoice.status}\n\n"
        "Ta wiadomosc zostala wygenerowana automatycznie przez system rozliczen licencji."
    )
    return subject, body


def _log_reminder(
    db: Session,
    *,
    tenant_id: int,
    invoice_id: int,
    reminder_kind: str,
    recipient: str | None,
    status: str,
    error_message: str | None = None,
) -> None:
    db.add(
        TenantBillingReminderLog(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            reminder_kind=reminder_kind,
            channel="EMAIL",
            recipient=recipient,
            status=status,
            error_message=(error_message or "")[:255] or None,
        )
    )


def process_billing_reminders(db: Session, *, now_utc: datetime | None = None) -> dict[str, int]:
    now_dt = now_utc or datetime.utcnow()
    today = now_dt.date()
    before_due_days = _parse_int_list(settings.BILLING_REMINDER_DAYS_BEFORE_DUE)
    after_due_days = _parse_int_list(settings.BILLING_REMINDER_DAYS_AFTER_DUE)
    sent = 0
    failed = 0

    tenants = db.query(Tenant).filter(Tenant.is_active.is_(True)).all()
    for tenant in tenants:
        if not tenant.billing_email:
            continue
        invoice = ensure_tenant_invoice(db, tenant.id, today.year, today.month)
        if invoice.paid_at:
            if invoice.status != "PAID":
                invoice.status = "PAID"
            continue
        if today > invoice.due_date:
            invoice.status = "OVERDUE"
        elif invoice.status != "OPEN":
            invoice.status = "OPEN"

        delta_days = (invoice.due_date - today).days
        reminder_kind: str | None = None
        if delta_days in before_due_days:
            reminder_kind = f"DUE_MINUS_{delta_days}"
        elif delta_days < 0:
            overdue_days = abs(delta_days)
            if overdue_days in after_due_days:
                reminder_kind = f"OVERDUE_{overdue_days}"
        if reminder_kind is None:
            continue

        exists = (
            db.query(TenantBillingReminderLog.id)
            .filter(
                TenantBillingReminderLog.invoice_id == invoice.id,
                TenantBillingReminderLog.reminder_kind == reminder_kind,
            )
            .first()
        )
        if exists:
            continue

        try:
            subject, body = _render_invoice_message(tenant, invoice, reminder_kind)
            send_billing_email(tenant.billing_email, subject, body)
            _log_reminder(
                db,
                tenant_id=tenant.id,
                invoice_id=invoice.id,
                reminder_kind=reminder_kind,
                recipient=tenant.billing_email,
                status="SENT",
            )
            if not invoice.sent_at:
                invoice.sent_at = now_dt
            sent += 1
        except Exception as exc:
            _log_reminder(
                db,
                tenant_id=tenant.id,
                invoice_id=invoice.id,
                reminder_kind=reminder_kind,
                recipient=tenant.billing_email,
                status="FAILED",
                error_message=str(exc),
            )
            failed += 1

    db.commit()
    return {"sent": sent, "failed": failed}


def _billing_worker() -> None:
    while True:
        db = SessionLocal()
        try:
            process_billing_reminders(db)
        except Exception:
            db.rollback()
        finally:
            db.close()
        time.sleep(max(300, int(settings.BILLING_REMINDER_POLL_SECONDS or 3600)))


def start_billing_scheduler() -> None:
    global _billing_scheduler_started
    if not is_smtp_configured():
        return
    with _billing_scheduler_lock:
        if _billing_scheduler_started:
            return
        thread = threading.Thread(target=_billing_worker, name="billing-reminder-worker", daemon=True)
        thread.start()
        _billing_scheduler_started = True
