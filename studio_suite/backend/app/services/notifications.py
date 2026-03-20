"""SMS notifications via Twilio."""
from __future__ import annotations

import base64
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.salon_core import (
    Appointment,
    AppointmentService,
    BundleCatalog,
    Customer,
    Notification,
    Salon,
    ServiceCatalogItem,
    SmsGatewayDevice,
)

REMINDER_POLL_SECONDS = 900
_scheduler_started = False
_scheduler_lock = threading.Lock()


def _sms_provider() -> str:
    return (settings.SMS_PROVIDER or "TWILIO").strip().upper()


def is_sms_configured() -> bool:
    provider = _sms_provider()
    if provider == "LOCAL_HTTP":
        if settings.LOCAL_SMS_URL:
            return True
        db = SessionLocal()
        try:
            row = db.query(SmsGatewayDevice.id).filter(SmsGatewayDevice.is_active.is_(True)).first()
            return bool(row)
        finally:
            db.close()
    if provider != "TWILIO":
        return False
    sid = settings.TWILIO_SID or settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_TOKEN or settings.TWILIO_AUTH_TOKEN
    return bool(sid and token and settings.TWILIO_PHONE_FROM)


def _normalize_phone(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    raw = raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if raw.startswith("00"):
        raw = f"+{raw[2:]}"
    if raw.startswith("+"):
        normalized = "+" + re.sub(r"\D", "", raw[1:])
        return normalized if len(normalized) >= 8 else None
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 9:
        return f"+48{digits}"
    if len(digits) >= 8:
        return f"+{digits}"
    return None


def _appointment_offer_label(db: Session, appointment: Appointment) -> str:
    if appointment.bundle_id:
        bundle = db.query(BundleCatalog).filter(BundleCatalog.id == appointment.bundle_id).first()
        if bundle:
            return bundle.name
    service_ids = [
        row.service_id
        for row in db.query(AppointmentService).filter(AppointmentService.appointment_id == appointment.id).all()
    ]
    if service_ids:
        services = (
            db.query(ServiceCatalogItem)
            .filter(ServiceCatalogItem.id.in_(service_ids))
            .order_by(ServiceCatalogItem.name.asc())
            .all()
        )
        if services:
            names = [row.name for row in services[:2]]
            suffix = " +" if len(services) > 2 else ""
            return ", ".join(names) + suffix
    return "wizyta"


def build_notification_message(
    db: Session,
    appointment: Appointment,
    notification_type: str,
) -> str:
    salon = db.query(Salon).filter(Salon.id == appointment.salon_id).first()
    start_label = appointment.start_at.strftime("%d.%m %H:%M")
    offer_label = _appointment_offer_label(db, appointment)
    salon_label = salon.name if salon else "Studio Suite"
    action_link = f"{settings.APP_PUBLIC_URL.rstrip('/')}/calendar?appointment_id={appointment.id}"
    if notification_type == "public_confirmed":
        return f"Twoja rezerwacja #{appointment.id} {start_label} {offer_label} {salon_label} potwierdzona!"
    if notification_type == "public_rejected":
        return f"Twoja rezerwacja #{appointment.id} {start_label} {offer_label} {salon_label} zostala odrzucona."
    if notification_type == "reminder_24h":
        return f"Przypomnienie: wizyta {start_label} {offer_label} {salon_label}. Szczegoly: {action_link}"
    return f"Wizyta {start_label} {offer_label} {salon_label}. Anuluj: {action_link}"


def _send_twilio_sms(phone: str, message: str) -> tuple[str, str]:
    sid = settings.TWILIO_SID or settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_TOKEN or settings.TWILIO_AUTH_TOKEN
    phone_from = settings.TWILIO_PHONE_FROM
    if not sid or not token or not phone_from:
        raise RuntimeError("Twilio credentials are not configured")

    auth = base64.b64encode(f"{sid}:{token}".encode("utf-8")).decode("ascii")
    body = urllib.parse.urlencode({
        "To": phone,
        "From": phone_from,
        "Body": message,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return str(payload.get("sid") or ""), str(payload.get("status") or "queued")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(detail or f"Twilio HTTP {exc.code}") from exc


def _resolve_local_sms_target(salon_id: int | None = None) -> tuple[str, str | None]:
    db = SessionLocal()
    try:
        query = db.query(SmsGatewayDevice).filter(SmsGatewayDevice.is_active.is_(True))
        if salon_id is not None:
            query = query.filter(SmsGatewayDevice.salon_id == int(salon_id))
        row = query.order_by(SmsGatewayDevice.last_seen_at.desc(), SmsGatewayDevice.created_at.desc()).first()
        if not row and salon_id is not None:
            row = (
                db.query(SmsGatewayDevice)
                .filter(SmsGatewayDevice.is_active.is_(True))
                .order_by(SmsGatewayDevice.last_seen_at.desc(), SmsGatewayDevice.created_at.desc())
                .first()
            )
        if not row:
            endpoint = (settings.LOCAL_SMS_URL or "").strip()
            token = (settings.LOCAL_SMS_TOKEN or "").strip() or None
            if endpoint:
                return endpoint, token
            raise RuntimeError("No active SMS gateway device")
        return row.endpoint_url, row.auth_token
    finally:
        db.close()


def _send_local_http_sms(phone: str, message: str, salon_id: int | None = None) -> tuple[str, str]:
    endpoint, device_token = _resolve_local_sms_target(salon_id)
    method = (settings.LOCAL_SMS_METHOD or "POST").strip().upper()
    timeout = max(3, int(settings.LOCAL_SMS_TIMEOUT_SECONDS or 20))

    headers = {
        "Content-Type": "application/json",
    }
    if device_token:
        headers["Authorization"] = f"Bearer {device_token}"

    request_data: bytes | None = None
    request_url = endpoint
    if method == "GET":
        query = urllib.parse.urlencode({"to": phone, "message": message})
        separator = "&" if "?" in endpoint else "?"
        request_url = f"{endpoint}{separator}{query}"
    else:
        request_data = json.dumps({"to": phone, "message": message}).encode("utf-8")

    last_error: Exception | None = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            request_url,
            data=request_data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore").strip()
                payload: dict[str, object] = {}
                if raw:
                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            payload = parsed
                    except json.JSONDecodeError:
                        payload = {}
                message_id = (
                    str(payload.get("message_id") or payload.get("id") or payload.get("sid") or "")
                    if payload
                    else ""
                )
                status_value = (
                    str(payload.get("status") or payload.get("state") or payload.get("result") or "queued")
                    if payload
                    else "queued"
                )
                return message_id, status_value
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            # 4xx usually means bad auth/payload, retrying will not help.
            if 400 <= int(exc.code) < 500:
                raise RuntimeError(detail or f"LOCAL_HTTP SMS gateway returned HTTP {exc.code}") from exc
            last_error = RuntimeError(detail or f"LOCAL_HTTP SMS gateway returned HTTP {exc.code}")
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LOCAL_HTTP SMS gateway unreachable: {exc.reason}")
        if attempt < max_attempts:
            time.sleep(0.25 * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError("LOCAL_HTTP SMS gateway unreachable")


def _send_sms(phone: str, message: str, salon_id: int | None = None) -> tuple[str, str]:
    provider = _sms_provider()
    if provider == "LOCAL_HTTP":
        return _send_local_http_sms(phone, message, salon_id)
    if provider == "TWILIO":
        return _send_twilio_sms(phone, message)
    raise RuntimeError(f"Unsupported SMS_PROVIDER: {provider}")


def send_sms_text(phone: str, message: str, salon_id: int | None = None) -> tuple[str, str]:
    normalized = _normalize_phone(phone)
    if not normalized:
        raise ValueError("missing_phone")
    if not message.strip():
        raise ValueError("missing_message")
    return _send_sms(normalized, message.strip(), salon_id)


def send_appointment_sms(
    db: Session,
    appointment_id: int,
    *,
    notification_type: str = "confirmation",
    override_phone: str | None = None,
) -> Notification:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise ValueError("appointment_not_found")
    customer = db.query(Customer).filter(Customer.id == appointment.client_id).first()
    if not customer:
        raise ValueError("customer_not_found")

    phone = _normalize_phone(override_phone or customer.phone)
    if not phone:
        raise ValueError("missing_phone")

    message = build_notification_message(db, appointment, notification_type)
    notification = Notification(
        appointment_id=appointment.id,
        phone=phone,
        notification_type=notification_type,
        status="pending",
        message=message,
    )
    db.add(notification)
    db.flush()

    try:
        provider_message_id, provider_status = _send_sms(phone, message, appointment.salon_id)
        notification.provider_message_id = provider_message_id or None
        notification.status = "sent" if provider_status in {"queued", "accepted", "sent", "delivered"} else provider_status[:16]
        notification.sent_at = datetime.utcnow()
        notification.error_message = None
    except Exception as exc:
        notification.status = "failed"
        notification.error_message = str(exc)[:255]

    db.commit()
    db.refresh(notification)
    return notification


def send_today_batch_sms(db: Session, salon_id: int) -> dict[str, int]:
    start = datetime.combine(datetime.now().date(), datetime.min.time())
    end = datetime.combine(datetime.now().date(), datetime.max.time())
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.salon_id == salon_id,
            Appointment.start_at >= start,
            Appointment.start_at <= end,
            Appointment.status.in_(["planned", "confirmed"]),
        )
        .order_by(Appointment.start_at.asc())
        .all()
    )
    sent = 0
    failed = 0
    for appointment in appointments:
        existing = (
            db.query(Notification.id)
            .filter(Notification.appointment_id == appointment.id, Notification.notification_type == "confirmation")
            .first()
        )
        if existing:
            continue
        notification = send_appointment_sms(db, appointment.id, notification_type="confirmation")
        if notification.status == "failed":
            failed += 1
        else:
            sent += 1
    return {"sent": sent, "failed": failed}


def process_due_reminders(db: Session) -> dict[str, int]:
    if not is_sms_configured():
        return {"sent": 0, "failed": 0}
    now = datetime.utcnow()
    window_start = now + timedelta(hours=23, minutes=30)
    window_end = now + timedelta(hours=24, minutes=30)
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.start_at >= window_start,
            Appointment.start_at <= window_end,
            Appointment.status.in_(["planned", "confirmed"]),
        )
        .order_by(Appointment.start_at.asc())
        .all()
    )
    sent = 0
    failed = 0
    for appointment in appointments:
        existing = (
            db.query(Notification.id)
            .filter(Notification.appointment_id == appointment.id, Notification.notification_type == "reminder_24h")
            .first()
        )
        if existing:
            continue
        notification = send_appointment_sms(db, appointment.id, notification_type="reminder_24h")
        if notification.status == "failed":
            failed += 1
        else:
            sent += 1
    return {"sent": sent, "failed": failed}


def _reminder_worker() -> None:
    while True:
        db = SessionLocal()
        try:
            process_due_reminders(db)
        except Exception:
            db.rollback()
        finally:
            db.close()
        time.sleep(REMINDER_POLL_SECONDS)


def start_notification_scheduler() -> None:
    global _scheduler_started
    if not is_sms_configured():
        return
    with _scheduler_lock:
        if _scheduler_started:
            return
        thread = threading.Thread(target=_reminder_worker, name="sms-reminder-worker", daemon=True)
        thread.start()
        _scheduler_started = True
