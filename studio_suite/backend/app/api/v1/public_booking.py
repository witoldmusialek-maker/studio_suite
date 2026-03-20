from __future__ import annotations

import hashlib
import json
import secrets
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    BundleCatalog,
    BundleCatalogItem,
    AppointmentResource,
    AppointmentService,
    PublicBookingOtpChallenge,
    Salon,
    SalonServiceCatalogItem,
    Customer,
    ServiceCatalogItem,
    StaffBundleOffer,
    StaffMember,
    StaffSalonMembership,
    StaffRole,
    StaffTimeOff,
    StaffMonthlySchedule,
    StaffWeeklySchedule,
)
from app.models.user import TenantModuleLicense
from app.schemas.public_booking import (
    PublicAppointmentCreate,
    PublicAppointmentRead,
    PublicBootstrapResponse,
    PublicBundleRead,
    PublicCalendarResponse,
    PublicOtpRequest,
    PublicOtpResponse,
    PublicSalonRead,
    PublicServiceRead,
    PublicStaffRead,
    PublicTimeSlot,
)
from app.services.notifications import is_sms_configured, send_sms_text

router = APIRouter(prefix="/public", tags=["public-booking"])

DEFAULT_START_HOUR = 8
DEFAULT_END_HOUR = 22
DEFAULT_SLOT_MINUTES = 30
MODULE_CODE_PUBLIC_BOOKING = "PUBLIC_BOOKING"


def _is_public_booking_enabled_for_tenant(db: Session, tenant_id: int) -> bool:
    row = (
        db.query(TenantModuleLicense.is_enabled)
        .filter(
            TenantModuleLicense.tenant_id == tenant_id,
            TenantModuleLicense.module_code == MODULE_CODE_PUBLIC_BOOKING,
        )
        .first()
    )
    # Backward-compatible: missing row means enabled.
    return True if row is None else bool(row[0])


def _assert_public_booking_enabled_for_salon(db: Session, salon_id: int) -> Salon:
    salon = db.query(Salon).filter(Salon.id == salon_id, Salon.is_active.is_(True)).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if not _is_public_booking_enabled_for_tenant(db, int(salon.tenant_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public booking is disabled for this salon")
    return salon


def _hash_otp(challenge_id: int, phone: str, code: str) -> str:
    payload = f"{challenge_id}:{phone}:{code}:{settings.SECRET_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mask_phone(phone: str) -> str:
    raw = (phone or "").strip()
    if len(raw) <= 4:
        return "***"
    return f"{raw[:2]}***{raw[-2:]}"


def _assert_public_rate_limits(db: Session, *, phone: str, request_ip: str | None) -> None:
    window_start = datetime.utcnow() - timedelta(minutes=15)
    phone_count = (
        db.query(PublicBookingOtpChallenge.id)
        .filter(
            PublicBookingOtpChallenge.phone == phone,
            PublicBookingOtpChallenge.created_at >= window_start,
        )
        .count()
    )
    if phone_count >= settings.PUBLIC_BOOKING_RATE_LIMIT_PHONE_PER_15M:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Za dużo prób dla numeru telefonu. Spróbuj ponownie później.")
    if request_ip:
        ip_count = (
            db.query(PublicBookingOtpChallenge.id)
            .filter(
                PublicBookingOtpChallenge.request_ip == request_ip,
                PublicBookingOtpChallenge.created_at >= window_start,
            )
            .count()
        )
        if ip_count >= settings.PUBLIC_BOOKING_RATE_LIMIT_IP_PER_15M:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Za dużo prób z tego adresu IP. Spróbuj ponownie później.")


def _bundle_duration_and_price(db: Session, bundle: BundleCatalog) -> tuple[int, float]:
    items = db.query(BundleCatalogItem).filter(BundleCatalogItem.bundle_id == bundle.id).all()
    service_ids = [row.service_id for row in items if row.service_id is not None]
    duration_minutes = 0
    if service_ids:
        service_rows = db.query(ServiceCatalogItem.id, ServiceCatalogItem.duration_minutes).filter(ServiceCatalogItem.id.in_(service_ids)).all()
        duration_by_id = {int(row.id): int(row.duration_minutes or 0) for row in service_rows}
        duration_minutes = sum(duration_by_id.get(int(service_id), 0) for service_id in service_ids)
    return max(30, duration_minutes or 30), float(bundle.price or 0)
def _staff_name(row: StaffMember) -> str:
    first_name = (row.first_name or "").strip()
    last_name = (row.last_name or "").strip()
    return f"{first_name} {last_name}".strip() or (row.display_name or f"#{row.id}")


def _staff_in_salon(db: Session, salon_id: int, preferred_staff_id: int | None = None) -> list[StaffMember]:
    allowed_role_codes = {"HAIRDRESSER", "MANICURIST"}
    query = (
        db.query(StaffMember)
        .outerjoin(StaffRole, StaffRole.id == StaffMember.role_id)
        .outerjoin(
            StaffSalonMembership,
            and_(
                StaffSalonMembership.staff_id == StaffMember.id,
                StaffSalonMembership.salon_id == salon_id,
                StaffSalonMembership.is_active.is_(True),
            ),
        )
        .filter(
            StaffMember.is_active.is_(True),
            StaffMember.can_be_booked.is_(True),
            func.upper(func.coalesce(StaffRole.code, "")).in_(allowed_role_codes),
            func.lower(func.coalesce(StaffMember.display_name, "")).notlike("%test%"),
            or_(StaffMember.salon_id == salon_id, StaffSalonMembership.id.isnot(None)),
        )
        .order_by(StaffMember.last_name.asc().nullslast(), StaffMember.first_name.asc().nullslast(), StaffMember.id.asc())
    )
    if preferred_staff_id is not None:
        query = query.filter(StaffMember.id == preferred_staff_id)
    return query.all()


def _subtract_interval(
    intervals: list[tuple[datetime, datetime]],
    start_at: datetime,
    end_at: datetime,
) -> list[tuple[datetime, datetime]]:
    result: list[tuple[datetime, datetime]] = []
    for current_start, current_end in intervals:
        if end_at <= current_start or start_at >= current_end:
            result.append((current_start, current_end))
            continue
        if start_at > current_start:
            result.append((current_start, start_at))
        if end_at < current_end:
            result.append((end_at, current_end))
    return result


def _has_conflict(start_at: datetime, end_at: datetime, intervals: list[tuple[datetime, datetime]]) -> bool:
    return any(start_at < busy_end and end_at > busy_start for busy_start, busy_end in intervals)


def _windows_for_staff(db: Session, salon_id: int, staff_id: int, target_date: date) -> list[tuple[datetime, datetime]]:
    monthly_schedules = (
        db.query(StaffMonthlySchedule)
        .filter(
            StaffMonthlySchedule.staff_id == staff_id,
            StaffMonthlySchedule.salon_id == salon_id,
            StaffMonthlySchedule.work_date == target_date,
            StaffMonthlySchedule.is_active.is_(True),
        )
        .order_by(StaffMonthlySchedule.time_from.asc())
        .all()
    )
    if monthly_schedules:
        windows = [
            (datetime.combine(target_date, row.time_from), datetime.combine(target_date, row.time_to))
            for row in monthly_schedules
        ]
    else:
        weekday = target_date.weekday()
        schedules = (
            db.query(StaffWeeklySchedule)
            .filter(
                StaffWeeklySchedule.staff_id == staff_id,
                StaffWeeklySchedule.salon_id == salon_id,
                StaffWeeklySchedule.weekday == weekday,
                StaffWeeklySchedule.is_active.is_(True),
            )
            .order_by(StaffWeeklySchedule.time_from.asc())
            .all()
        )
        if schedules:
            windows = [
                (datetime.combine(target_date, row.time_from), datetime.combine(target_date, row.time_to))
                for row in schedules
            ]
        else:
            windows = []

    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)
    time_off_rows = (
        db.query(StaffTimeOff)
        .filter(
            StaffTimeOff.staff_id == staff_id,
            StaffTimeOff.salon_id == salon_id,
            StaffTimeOff.start_datetime < day_end,
            StaffTimeOff.end_datetime > day_start,
        )
        .all()
    )
    for row in time_off_rows:
        windows = _subtract_interval(windows, row.start_datetime, row.end_datetime)
    return windows


def _busy_by_staff(db: Session, salon_id: int, day_start: datetime, day_end: datetime) -> dict[int, list[tuple[datetime, datetime]]]:
    busy: dict[int, list[tuple[datetime, datetime]]] = {}
    rows = (
        db.query(AppointmentResource.staff_id, Appointment.start_at, Appointment.end_at)
        .join(Appointment, Appointment.id == AppointmentResource.appointment_id)
        .filter(
            Appointment.salon_id == salon_id,
            Appointment.start_at < day_end,
            Appointment.end_at > day_start,
            Appointment.allow_overlap.is_(False),
            Appointment.status.in_(["pending", "planned", "confirmed", "started", "in_progress"]),
        )
        .all()
    )
    for staff_id, start_at, end_at in rows:
        busy.setdefault(int(staff_id), []).append((start_at, end_at))
    return busy


def _service_price(db: Session, salon_id: int, service: ServiceCatalogItem) -> float:
    # For now use the catalog default; public booking should not expose legacy price matrix complexity.
    del salon_id
    return float(service.default_price or 0)


def _validate_public_offer_payload(
    db: Session,
    *,
    salon_id: int,
    service_id: int | None,
    bundle_id: int | None,
    staff_id: int,
    slot: datetime,
) -> tuple[ServiceCatalogItem | None, BundleCatalog | None, int, float]:
    if bool(service_id) == bool(bundle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wybierz dokładnie: usługę albo forfet.")
    salon = _assert_public_booking_enabled_for_salon(db, salon_id)
    staff_allowed = {row.id for row in _staff_in_salon(db, salon_id, preferred_staff_id=staff_id)}
    if staff_id not in staff_allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff does not belong to this salon")

    service: ServiceCatalogItem | None = None
    bundle: BundleCatalog | None = None
    if service_id is not None:
        service = (
            db.query(ServiceCatalogItem)
            .filter(ServiceCatalogItem.id == service_id, ServiceCatalogItem.is_active.is_(True), ServiceCatalogItem.bookable.is_(True))
            .first()
        )
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        duration = max(30, int(service.duration_minutes or 30))
        price = float(service.default_price or 0)
    else:
        bundle = (
            db.query(BundleCatalog)
            .filter(
                BundleCatalog.id == bundle_id,
                BundleCatalog.salon_id == salon_id,
            )
            .first()
        )
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        personal_offer_exists = (
            db.query(StaffBundleOffer.id)
            .filter(
                StaffBundleOffer.tenant_id == salon.tenant_id,
                StaffBundleOffer.salon_id == salon_id,
                StaffBundleOffer.staff_id == staff_id,
                StaffBundleOffer.bundle_id == bundle_id,
                StaffBundleOffer.is_active.is_(True),
            )
            .first()
        )
        if not personal_offer_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wybrany forfet nie jest dostępny u tego specjalisty.")
        duration, price = _bundle_duration_and_price(db, bundle)

    start_at = slot.replace(second=0, microsecond=0)
    end_at = start_at + timedelta(minutes=duration)
    day_start = datetime.combine(start_at.date(), time.min)
    day_end = datetime.combine(start_at.date(), time.max)
    busy = _busy_by_staff(db, salon_id, day_start, day_end).get(staff_id, [])
    if _has_conflict(start_at, end_at, busy):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected slot is no longer available")
    return service, bundle, duration, price


@router.get("/bootstrap", response_model=PublicBootstrapResponse)
async def public_bootstrap(
    salon_id: int | None = None,
    staff_id: int | None = None,
    db: Session = Depends(get_db),
):
    salons_all = db.query(Salon).filter(Salon.is_active.is_(True)).order_by(Salon.name.asc()).all()
    salons = [row for row in salons_all if _is_public_booking_enabled_for_tenant(db, int(row.tenant_id))]
    if salon_id is not None:
        selected_salon = next((row for row in salons if row.id == salon_id), None)
        if selected_salon is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    selected_salon_id = salon_id or (salons[0].id if salons else None)
    services_query = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.is_active.is_(True), ServiceCatalogItem.bookable.is_(True))
        .order_by(ServiceCatalogItem.name.asc())
    )
    if selected_salon_id is not None:
        assigned_service_ids = [
            row[0]
            for row in db.query(SalonServiceCatalogItem.service_id)
            .filter(
                SalonServiceCatalogItem.salon_id == selected_salon_id,
                SalonServiceCatalogItem.is_active.is_(True),
            )
            .all()
        ]
        if assigned_service_ids:
            services_query = services_query.filter(ServiceCatalogItem.id.in_(assigned_service_ids))
    services = services_query.limit(300).all()
    staff = _staff_in_salon(db, selected_salon_id) if selected_salon_id is not None else []
    bundles: list[BundleCatalog] = []
    # Public flow: bundles are always specialist-specific.
    if selected_salon_id is not None and staff_id is not None:
        bundle_query = db.query(BundleCatalog).filter(BundleCatalog.salon_id == selected_salon_id)
        selected_salon = db.query(Salon).filter(Salon.id == selected_salon_id).first()
        if selected_salon:
            offer_bundle_ids = [
                row[0]
                for row in db.query(StaffBundleOffer.bundle_id)
                .filter(
                    StaffBundleOffer.tenant_id == selected_salon.tenant_id,
                    StaffBundleOffer.salon_id == selected_salon_id,
                    StaffBundleOffer.staff_id == staff_id,
                    StaffBundleOffer.is_active.is_(True),
                )
                .order_by(StaffBundleOffer.priority.asc(), StaffBundleOffer.id.asc())
                .all()
            ]
            if offer_bundle_ids:
                bundle_query = bundle_query.filter(BundleCatalog.id.in_(offer_bundle_ids))
            else:
                bundle_query = bundle_query.filter(BundleCatalog.id == -1)
            bundles = bundle_query.order_by(BundleCatalog.name.asc()).limit(200).all()
    return PublicBootstrapResponse(
        salons=[PublicSalonRead(id=row.id, name=row.name) for row in salons],
        services=[
            PublicServiceRead(
                id=row.id,
                code=row.legacy_code,
                name=row.name,
                duration_minutes=max(30, int(row.duration_minutes or 30)),
                price=_service_price(db, selected_salon_id or 0, row),
            )
            for row in services
        ],
        bundles=[
            PublicBundleRead(
                id=row.id,
                code=row.legacy_code,
                name=row.name,
                price=float(row.price or 0),
                duration_minutes=_bundle_duration_and_price(db, row)[0],
            )
            for row in bundles
        ],
        staff=[
            PublicStaffRead(
                id=row.id,
                display_name=_staff_name(row),
                public_bio=(row.public_bio or None),
                public_photo_url=(
                    row.public_photo_url
                    or (f"/api/v1/public/staff/{row.id}/photo?salon_id={selected_salon_id}" if selected_salon_id and row.public_photo_data else None)
                ),
            )
            for row in staff
        ],
    )


@router.get("/staff/{staff_id}/photo")
async def public_staff_photo(
    staff_id: int,
    salon_id: int,
    db: Session = Depends(get_db),
):
    _assert_public_booking_enabled_for_salon(db, salon_id)
    row = (
        db.query(StaffMember)
        .outerjoin(
            StaffSalonMembership,
            and_(
                StaffSalonMembership.staff_id == StaffMember.id,
                StaffSalonMembership.salon_id == salon_id,
                StaffSalonMembership.is_active.is_(True),
            ),
        )
        .filter(
            StaffMember.id == staff_id,
            StaffMember.is_active.is_(True),
            StaffMember.can_be_booked.is_(True),
            or_(StaffMember.salon_id == salon_id, StaffSalonMembership.id.isnot(None)),
        )
        .first()
    )
    if not row or not row.public_photo_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zdjęcie pracownika nie istnieje")
    return Response(content=bytes(row.public_photo_data), media_type=row.public_photo_content_type or "image/jpeg")


@router.get("/calendar", response_model=PublicCalendarResponse)
async def public_calendar(
    salon_id: int,
    service_id: int | None = None,
    bundle_id: int | None = None,
    staff_id: int | None = None,
    duration_minutes: int = 30,
    days: int = Query(default=7, ge=1, le=14),
    db: Session = Depends(get_db),
):
    salon = _assert_public_booking_enabled_for_salon(db, salon_id)

    if bool(service_id) and bool(bundle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wybierz usługę albo forfet.")
    if service_id is not None:
        service = (
            db.query(ServiceCatalogItem)
            .filter(ServiceCatalogItem.id == service_id, ServiceCatalogItem.is_active.is_(True), ServiceCatalogItem.bookable.is_(True))
            .first()
        )
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        effective_duration = max(30, int(service.duration_minutes or 30))
    elif bundle_id is not None:
        bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id, BundleCatalog.salon_id == salon_id).first()
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        effective_duration, _ = _bundle_duration_and_price(db, bundle)
    else:
        effective_duration = 60 if int(duration_minutes or 30) >= 60 else 30

    staff_rows = _staff_in_salon(db, salon_id, preferred_staff_id=staff_id)
    if staff_id is not None and not staff_rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not available in salon")

    slots: list[PublicTimeSlot] = []
    today = datetime.now().date()
    for day_offset in range(days):
        target_date = today + timedelta(days=day_offset)
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)
        busy = _busy_by_staff(db, salon_id, day_start, day_end)
        for staff_row in staff_rows:
            windows = _windows_for_staff(db, salon_id, staff_row.id, target_date)
            for window_start, window_end in windows:
                cursor = window_start
                while cursor + timedelta(minutes=effective_duration) <= window_end:
                    candidate_end = cursor + timedelta(minutes=effective_duration)
                    if cursor >= datetime.now() and not _has_conflict(cursor, candidate_end, busy.get(staff_row.id, [])):
                        slots.append(
                            PublicTimeSlot(
                                staff_id=staff_row.id,
                                staff_name=_staff_name(staff_row),
                                start_at=cursor,
                                end_at=candidate_end,
                                duration_minutes=effective_duration,
                            )
                        )
                    cursor += timedelta(minutes=DEFAULT_SLOT_MINUTES)
    slots.sort(key=lambda row: (row.start_at, row.staff_name))
    return PublicCalendarResponse(salon_id=salon_id, duration_minutes=effective_duration, slots=slots)


@router.post("/otp/request", response_model=PublicOtpResponse)
async def request_public_booking_otp(
    payload: PublicOtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    normalized_phone = (payload.client_phone or "").strip()
    if not normalized_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="client_phone is required")

    service, bundle, duration_minutes, price = _validate_public_offer_payload(
        db,
        salon_id=payload.salon_id,
        service_id=payload.service_id,
        bundle_id=payload.bundle_id,
        staff_id=payload.staff_id,
        slot=payload.slot,
    )
    salon = _assert_public_booking_enabled_for_salon(db, payload.salon_id)
    request_ip = request.client.host if request.client else None
    _assert_public_rate_limits(db, phone=normalized_phone, request_ip=request_ip)

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(seconds=settings.PUBLIC_BOOKING_OTP_TTL_SECONDS)
    challenge = PublicBookingOtpChallenge(
        tenant_id=salon.tenant_id,
        salon_id=payload.salon_id,
        phone=normalized_phone,
        otp_hash="pending",
        expires_at=expires_at,
        request_ip=request_ip,
        payload_json=json.dumps(
            {
                "salon_id": payload.salon_id,
                "service_id": payload.service_id,
                "bundle_id": payload.bundle_id,
                "staff_id": payload.staff_id,
                "slot": payload.slot.isoformat(),
                "client_phone": normalized_phone,
                "client_name": (payload.client_name or "").strip(),
                "duration_minutes": duration_minutes,
                "price": price,
                "offer_label": service.name if service is not None else (bundle.name if bundle is not None else "wizyta"),
            }
        ),
    )
    db.add(challenge)
    db.flush()
    challenge.otp_hash = _hash_otp(challenge.id, normalized_phone, otp_code)

    if not settings.PUBLIC_BOOKING_REQUIRE_OTP:
        challenge.verified_at = datetime.utcnow()
        db.commit()
        return PublicOtpResponse(
            otp_challenge_id=challenge.id,
            expires_in_seconds=settings.PUBLIC_BOOKING_OTP_TTL_SECONDS,
            masked_phone=_mask_phone(normalized_phone),
        )

    if not is_sms_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OTP SMS is not configured")
    sms_message = f"Kod potwierdzający rezerwację: {otp_code}. Ważny {max(settings.PUBLIC_BOOKING_OTP_TTL_SECONDS // 60, 1)} min."
    try:
        send_sms_text(normalized_phone, sms_message, salon_id=payload.salon_id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Nie udało się wysłać SMS OTP: {exc}") from exc

    db.commit()
    return PublicOtpResponse(
        otp_challenge_id=challenge.id,
        expires_in_seconds=settings.PUBLIC_BOOKING_OTP_TTL_SECONDS,
        masked_phone=_mask_phone(normalized_phone),
    )


@router.post("/appointments", response_model=PublicAppointmentRead, status_code=status.HTTP_201_CREATED)
async def public_create_appointment(
    payload: PublicAppointmentCreate,
    db: Session = Depends(get_db),
):
    service, bundle, duration_minutes, price = _validate_public_offer_payload(
        db,
        salon_id=payload.salon_id,
        service_id=payload.service_id,
        bundle_id=payload.bundle_id,
        staff_id=payload.staff_id,
        slot=payload.slot,
    )
    salon = _assert_public_booking_enabled_for_salon(db, payload.salon_id)

    start_at = payload.slot.replace(second=0, microsecond=0)
    end_at = start_at + timedelta(minutes=duration_minutes)

    normalized_phone = (payload.client_phone or "").strip()
    if not normalized_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="client_phone is required")

    if settings.PUBLIC_BOOKING_REQUIRE_OTP:
        if not payload.otp_challenge_id or not payload.otp_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wymagane potwierdzenie OTP.")
        challenge = db.query(PublicBookingOtpChallenge).filter(
            PublicBookingOtpChallenge.id == payload.otp_challenge_id,
            PublicBookingOtpChallenge.tenant_id == salon.tenant_id,
            PublicBookingOtpChallenge.salon_id == payload.salon_id,
            PublicBookingOtpChallenge.phone == normalized_phone,
        ).first()
        if not challenge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wyzwanie OTP nie znalezione.")
        if challenge.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Kod OTP wygasł.")
        if challenge.verified_at is None:
            if challenge.attempts_count >= settings.PUBLIC_BOOKING_OTP_MAX_ATTEMPTS:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Przekroczono liczbę prób OTP.")
            if challenge.otp_hash != _hash_otp(challenge.id, normalized_phone, (payload.otp_code or "").strip()):
                challenge.attempts_count += 1
                challenge.last_attempt_at = datetime.utcnow()
                db.commit()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nieprawidłowy kod OTP.")
            try:
                source_payload = json.loads(challenge.payload_json or "{}")
            except Exception:
                source_payload = {}
            expected_slot = str(source_payload.get("slot") or "")
            if expected_slot and expected_slot != payload.slot.isoformat():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dane rezerwacji różnią się od żądania OTP.")
            if int(source_payload.get("staff_id") or 0) != payload.staff_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dane rezerwacji różnią się od żądania OTP.")
            if int(source_payload.get("salon_id") or 0) != payload.salon_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dane rezerwacji różnią się od żądania OTP.")
            challenge.verified_at = datetime.utcnow()
            challenge.last_attempt_at = datetime.utcnow()
            challenge.attempts_count += 1
            db.flush()

    customer = (
        db.query(Customer)
        .filter(func.coalesce(Customer.phone, "") == normalized_phone)
        .order_by(Customer.id.desc())
        .first()
    )
    if not customer:
        display_name = (payload.client_name or "").strip() or f"Klient {normalized_phone}"
        parts = display_name.split(maxsplit=1)
        customer = Customer(
            display_name=display_name,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else None,
            phone=normalized_phone,
        )
        db.add(customer)
        db.flush()

    appointment = Appointment(
        tenant_id=salon.tenant_id,
        salon_id=payload.salon_id,
        client_id=customer.id,
        start_at=start_at,
        end_at=end_at,
        status="pending",
        allow_overlap=False,
        bundle_id=(bundle.id if bundle else None),
        total_price_snapshot=price,
    )
    db.add(appointment)
    db.flush()
    db.add(AppointmentResource(appointment_id=appointment.id, staff_id=payload.staff_id))
    if service is not None:
        db.add(AppointmentService(appointment_id=appointment.id, service_id=service.id))
    elif bundle is not None:
        bundle_items = db.query(BundleCatalogItem).filter(BundleCatalogItem.bundle_id == bundle.id).order_by(BundleCatalogItem.position.asc()).all()
        for item in bundle_items:
            if item.service_id is not None:
                db.add(AppointmentService(appointment_id=appointment.id, service_id=item.service_id))
    db.commit()
    return PublicAppointmentRead(
        appointment_id=appointment.id,
        status=appointment.status,
        salon_id=appointment.salon_id,
        service_id=(service.id if service else None),
        bundle_id=(bundle.id if bundle else None),
        staff_id=payload.staff_id,
        start_at=appointment.start_at,
        end_at=appointment.end_at,
        client_phone=normalized_phone,
    )
