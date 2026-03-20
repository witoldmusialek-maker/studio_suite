"""
Booking endpoints used by calendar/clients dashboard.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    PerformedLineResource,
    AppointmentResource,
    AppointmentService,
    AppointmentServiceStep,
    BundleCatalog,
    BundleCatalogItem,
    ClientCard,
    Customer,
    Invitation,
    LegacyProductCatalogItem,
    Payment,
    Salon,
    Sale,
    ServiceCatalogItem,
    ServiceRecipeItem,
    StaffMember,
    StaffBundleOffer,
    StaffSalonMembership,
    StaffTimeOff,
    StaffRole,
    StaffMonthlySchedule,
    StaffWeeklySchedule,
)
from app.models.user import User, UserRole
from app.schemas.booking import (
    BookingAppointment,
    BookingAppointmentComplete,
    BookingAppointmentCreate,
    BookingAvailabilityResponse,
    BookingAvailabilitySlot,
    BookingAvailabilityStaffSlots,
    BookingBootstrapResponse,
    BookingBundle,
    BookingBundleItem,
    BookingClient,
    BookingClientCreate,
    BookingClientUpdate,
    BookingColorProduct,
    BookingSmsBatchResponse,
    BookingSmsNotifyRequest,
    BookingSmsNotifyResponse,
    BookingPerformedServiceLine,
    BookingPerformedLineResourceRead,
    BookingPriceListItem,
    BookingSalon,
    BookingService,
    BookingSalonStaffMember,
    BookingStaffLocationRead,
    BookingStaffLocationWrite,
    BookingStaffBundleOfferRead,
    BookingStaffBundleOfferWrite,
    BookingStaffResource,
    BookingStaffRole,
    BookingStatsResponse,
    BookingStaffTimeOffCreate,
    BookingStaffTimeOffRead,
    BookingStaffTimeOffUpdate,
    BookingStaffWeeklyScheduleCreate,
    BookingStaffMonthlyScheduleRead,
    BookingStaffMonthlyScheduleReplace,
    BookingStaffWeeklyScheduleRead,
    BookingStaffWeeklyScheduleUpdate,
)
from app.services.legacy_catalog_service import get_legacy_catalog, get_legacy_products
from app.services.notifications import send_appointment_sms, send_today_batch_sms

router = APIRouter(prefix="/booking", tags=["booking"])


def _to_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="minutes")


def _validate_not_backdated(start_at: datetime) -> None:
    now = datetime.now(start_at.tzinfo) if start_at.tzinfo else datetime.now()
    grace_minutes = max(0, int(getattr(settings, "BOOKING_BACKDATE_GRACE_MINUTES", 0)))
    threshold = now - timedelta(minutes=grace_minutes)
    if start_at < threshold:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nie mozna rezerwowac wstecz. Dostepny czas od: {threshold.strftime('%Y-%m-%d %H:%M')}",
        )


def _to_client(customer: Customer) -> BookingClient:
    return BookingClient(
        id=customer.id,
        full_name=customer.display_name,
        phone=customer.phone or "",
        email=customer.email,
    )


def _normalize_staff_full_name(row: StaffMember) -> str:
    first_name = (row.first_name or "").strip()
    last_name = (row.last_name or "").strip()
    return f"{first_name} {last_name}".strip()


def _estimate_product_unit_cost(product: LegacyProductCatalogItem | None) -> Decimal:
    if product is None:
        return Decimal("0")
    for candidate in (product.purchase_price, product.purchase_price_c, product.catalog_net_price):
        if candidate is not None:
            return Decimal(str(candidate))
    return Decimal("0")


def _to_appointment(row: Appointment, resources_by_appointment: dict[int, list[int]], services_by_appointment: dict[int, list[int]]) -> BookingAppointment:
    return BookingAppointment(
        id=row.id,
        salon_id=row.salon_id,
        client_id=row.client_id,
        start_at=_to_iso(row.start_at),
        end_at=_to_iso(row.end_at),
        status=row.status,
        allow_overlap=bool(getattr(row, "allow_overlap", False)),
        resources=resources_by_appointment.get(row.id, []),
        services=services_by_appointment.get(row.id, []),
        bundle_id=row.bundle_id,
        total_price_snapshot=float(row.total_price_snapshot or 0),
    )


def _matches_recipe_family(recipe_family: str | None, product: LegacyProductCatalogItem | None) -> bool:
    if not recipe_family or product is None:
        return True
    family_token = recipe_family.strip().lower().replace("_", " ")
    product_family = (product.family_code or "").strip().lower().replace("_", " ")
    product_name = (product.name or "").strip().lower()
    product_name_pl = (product.name_pl or "").strip().lower()
    return (
        family_token in product_family
        or family_token in product_name
        or family_token in product_name_pl
    )


def _resolve_date_filter(value: str | None) -> tuple[datetime, datetime] | None:
    if not value:
        return None
    lowered = value.strip().lower()
    today = datetime.now().date()
    if lowered == "today":
        target = today
    elif lowered == "tomorrow":
        target = today + timedelta(days=1)
    else:
        try:
            target = datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date filter") from exc
    return datetime.combine(target, time.min), datetime.combine(target, time.max)


def _load_appointments(db: Session, tenant_id: int) -> tuple[list[Appointment], dict[int, list[int]], dict[int, list[int]]]:
    appointments = db.query(Appointment).filter(Appointment.tenant_id == tenant_id).order_by(Appointment.start_at.desc()).all()
    appointment_ids = [row.id for row in appointments]

    resources_by_appointment: dict[int, list[int]] = {}
    resource_links = (
        db.query(AppointmentResource)
        .filter(AppointmentResource.appointment_id.in_(appointment_ids) if appointment_ids else False)
        .all()
    )
    for link in resource_links:
        resources_by_appointment.setdefault(link.appointment_id, []).append(link.staff_id)

    services_by_appointment: dict[int, list[int]] = {}
    service_links = (
        db.query(AppointmentService)
        .filter(AppointmentService.appointment_id.in_(appointment_ids) if appointment_ids else False)
        .all()
    )
    for link in service_links:
        services_by_appointment.setdefault(link.appointment_id, []).append(link.service_id)

    return appointments, resources_by_appointment, services_by_appointment


def _current_staff_member(db: Session, user: User) -> StaffMember | None:
    return db.query(StaffMember).filter(
        StaffMember.user_id == user.id,
        StaffMember.tenant_id == user.tenant_id,
    ).first()


def _staff_allowed_salons(db: Session, staff_member: StaffMember | None) -> set[int]:
    if staff_member is None:
        return set()
    allowed: set[int] = set()
    if staff_member.salon_id:
        allowed.add(staff_member.salon_id)
    memberships = (
        db.query(StaffSalonMembership.salon_id)
        .filter(
            StaffSalonMembership.staff_id == staff_member.id,
            StaffSalonMembership.is_active.is_(True),
        )
        .all()
    )
    allowed.update(int(row[0]) for row in memberships)
    return allowed


def _require_salon_access(db: Session, current_user: User, salon_id: int) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    staff_member = _current_staff_member(db, current_user)
    allowed_salons = _staff_allowed_salons(db, staff_member)
    if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not allowed_salons:
        return
    if salon_id not in allowed_salons:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this salon")


def _staff_in_salon(db: Session, salon_id: int, tenant_id: int) -> list[StaffMember]:
    return (
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
            StaffMember.tenant_id == tenant_id,
            StaffMember.is_active.is_(True),
            or_(StaffMember.salon_id == salon_id, StaffSalonMembership.id.isnot(None)),
        )
        .order_by(StaffMember.display_name.asc())
        .all()
    )


def _to_salon_staff_member(db: Session, row: StaffMember) -> BookingSalonStaffMember:
    role_code = None
    if row.role_id is not None:
        role = db.query(StaffRole).filter(StaffRole.id == row.role_id).first()
        role_code = role.code if role else None
    return BookingSalonStaffMember(
        id=row.id,
        user_id=row.user_id,
        role_id=row.role_id,
        role_code=role_code,
        salon_id=row.salon_id,
        display_name=_normalize_staff_full_name(row),
        first_name=row.first_name,
        last_name=row.last_name,
        can_be_booked=bool(row.can_be_booked),
        is_active=bool(row.is_active),
    )


def _require_staff_access(db: Session, current_user: User, staff: StaffMember) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    staff_salons = _staff_allowed_salons(db, staff)
    if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not staff_salons:
        return
    caller_staff = _current_staff_member(db, current_user)
    caller_salons = _staff_allowed_salons(db, caller_staff)
    if not caller_salons.intersection(staff_salons):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this staff member")


def _load_service_ids_for_duration(
    db: Session,
    service_ids: list[int] | None,
    bundle_id: int | None,
    salon_id: int,
) -> list[int]:
    resolved: list[int] = []
    if service_ids:
        resolved.extend(int(service_id) for service_id in service_ids)
    if bundle_id is not None:
        bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        if bundle.salon_id is not None and bundle.salon_id != salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bundle does not belong to salon")
        bundle_items = (
            db.query(BundleCatalogItem.service_id)
            .filter(BundleCatalogItem.bundle_id == bundle_id, BundleCatalogItem.service_id.isnot(None))
            .order_by(BundleCatalogItem.position.asc())
            .all()
        )
        resolved.extend(int(row[0]) for row in bundle_items)
    return resolved


def _calc_total_duration(db: Session, service_ids: list[int]) -> int:
    if not service_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="service_ids or bundle_id required")
    durations = (
        db.query(ServiceCatalogItem.id, ServiceCatalogItem.duration_minutes)
        .filter(ServiceCatalogItem.id.in_(service_ids))
        .all()
    )
    duration_by_id = {int(row[0]): int(row[1] or 0) for row in durations}
    missing = [sid for sid in service_ids if sid not in duration_by_id]
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service not found: {missing}")
    total = sum(max(0, duration_by_id[sid]) for sid in service_ids)
    return max(15, total)


def _subtract_interval(
    slots: list[tuple[datetime, datetime]],
    block_start: datetime,
    block_end: datetime,
) -> list[tuple[datetime, datetime]]:
    if block_end <= block_start:
        return slots
    result: list[tuple[datetime, datetime]] = []
    for start, end in slots:
        if block_end <= start or block_start >= end:
            result.append((start, end))
            continue
        if block_start > start:
            result.append((start, block_start))
        if block_end < end:
            result.append((block_end, end))
    return result


def _has_conflict(start_at: datetime, end_at: datetime, busy: list[tuple[datetime, datetime]]) -> bool:
    for bstart, bend in busy:
        if start_at < bend and end_at > bstart:
            return True
    return False


def _staff_work_windows_for_day(
    db: Session,
    *,
    staff_id: int,
    salon_id: int,
    day: date,
) -> list[tuple[datetime, datetime]]:
    day_slots: list[tuple[datetime, datetime]] = []
    monthly_schedules = (
        db.query(StaffMonthlySchedule)
        .filter(
            StaffMonthlySchedule.staff_id == staff_id,
            StaffMonthlySchedule.salon_id == salon_id,
            StaffMonthlySchedule.work_date == day,
            StaffMonthlySchedule.is_active.is_(True),
        )
        .order_by(StaffMonthlySchedule.time_from.asc())
        .all()
    )
    if monthly_schedules:
        for schedule in monthly_schedules:
            day_slots.append(
                (
                    datetime.combine(day, schedule.time_from),
                    datetime.combine(day, schedule.time_to),
                )
            )
    else:
        weekday = day.weekday()
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
        for schedule in schedules:
            day_slots.append(
                (
                    datetime.combine(day, schedule.time_from),
                    datetime.combine(day, schedule.time_to),
                )
            )

    day_start = datetime.combine(day, time.min)
    day_end = datetime.combine(day, time.max)
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
        day_slots = _subtract_interval(day_slots, row.start_datetime, row.end_datetime)
    return day_slots


def _count_available_staff(db: Session, salon_ids: list[int] | None = None) -> int:
    query = db.query(func.count(StaffMember.id)).filter(
        StaffMember.is_active.is_(True),
        StaffMember.can_be_booked.is_(True),
    )
    if salon_ids:
        query = query.filter(StaffMember.salon_id.in_(salon_ids))
    return int(query.scalar() or 0)


@router.get("/bootstrap", response_model=BookingBootstrapResponse)
async def get_bootstrap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    salons = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).order_by(Salon.name.asc()).all()
    staff_roles = db.query(StaffRole).order_by(StaffRole.name.asc()).all()
    staff_rows = db.query(StaffMember).filter(StaffMember.tenant_id == current_user.tenant_id).order_by(StaffMember.display_name.asc()).all()
    customers = db.query(Customer).filter(Customer.tenant_id == current_user.tenant_id).order_by(Customer.display_name.asc()).all()

    services_by_id: dict[int, BookingService] = {}
    price_items: list[BookingPriceListItem] = []
    bundles: list[BookingBundle] = []
    color_products_by_id: dict[int, BookingColorProduct] = {}

    price_item_id = 1
    for salon in salons:
        catalog = get_legacy_catalog(db, salon_id=salon.id)
        for row in catalog.get("service_prices", []):
            service_id = int(row["service_id"])
            services_by_id.setdefault(
                service_id,
                BookingService(
                    id=service_id,
                    code=str(row["service_code"]),
                    name=str(row["service_name"]),
                    duration_minutes=int(row.get("duration_minutes") or 0),
                ),
            )
            price_items.append(
                BookingPriceListItem(
                    id=price_item_id,
                    salon_id=int(row["salon_id"]),
                    service_id=service_id,
                    price=float(row.get("price") or 0),
                )
            )
            price_item_id += 1

        for bundle_row in catalog.get("bundles", []):
            items = [
                BookingBundleItem(
                    service_id=int(item["service_id"]),
                    override_price=float(item["override_price"]) if item.get("override_price") is not None else None,
                )
                for item in bundle_row.get("items", [])
                if item.get("service_id") is not None
            ]
            bundles.append(
                BookingBundle(
                    id=int(bundle_row["bundle_id"]),
                    salon_id=int(bundle_row["salon_id"]),
                    code=str(bundle_row["bundle_code"]),
                    name=str(bundle_row["bundle_name"]),
                    price=float(bundle_row.get("price") or 0),
                    items=items,
                )
            )

        for product in get_legacy_products(db, salon_id=salon.id):
            pid = int(product["product_id"])
            if pid in color_products_by_id:
                continue
            color_products_by_id[pid] = BookingColorProduct(
                id=pid,
                code=str(product["product_code"]),
                name=str(product["product_name"]),
                brand=str(product.get("brand") or ""),
            )

    resources = [
        BookingStaffResource(
            id=row.id,
            salon_id=int(row.salon_id),
            name=_normalize_staff_full_name(row),
            role_ids=[int(row.role_id)] if row.role_id is not None else [],
        )
        for row in staff_rows
        if row.salon_id is not None
    ]

    appointments, resources_by_appointment, services_by_appointment = _load_appointments(db, current_user.tenant_id)

    lines = db.query(AppointmentPerformedLine).order_by(AppointmentPerformedLine.id.asc()).all()

    return BookingBootstrapResponse(
        salons=[
            BookingSalon(id=row.id, code=row.code, name=row.name, is_active=bool(row.is_active))
            for row in salons
        ],
        staffRoles=[
            BookingStaffRole(id=row.id, code=row.code, name=row.name)
            for row in staff_roles
        ],
        resources=resources,
        clients=[_to_client(row) for row in customers],
        services=sorted(services_by_id.values(), key=lambda item: item.code),
        priceListItems=price_items,
        bundles=sorted(bundles, key=lambda item: (item.salon_id, item.code)),
        colorProducts=sorted(color_products_by_id.values(), key=lambda item: item.code),
        appointments=[
            _to_appointment(row, resources_by_appointment, services_by_appointment)
            for row in appointments
        ],
        performedServiceLines=[
            BookingPerformedServiceLine(
                id=row.id,
                appointment_id=row.appointment_id,
                service_id=row.service_id,
                service_name_snapshot=row.service_name_snapshot,
                worker_id=row.worker_id,
                worker_role_id=row.worker_role_id,
                list_price_snapshot=float(row.list_price_snapshot) if row.list_price_snapshot is not None else None,
                discount_allocated_snapshot=float(row.discount_allocated_snapshot) if row.discount_allocated_snapshot is not None else None,
                sold_as_bundle=bool(getattr(row, "sold_as_bundle", False)),
                bundle_id_snapshot=row.bundle_id_snapshot,
                price_snapshot=float(row.price_snapshot or 0),
                performed_at=_to_iso(row.performed_at),
                color_product_id=row.color_product_id,
            )
            for row in lines
        ],
    )


@router.get("/stats", response_model=BookingStatsResponse)
async def get_booking_stats(
    aggregate: str | None = None,
    salon_id: int | None = None,
    date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visible_salons = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()
    if current_user.role != UserRole.ADMIN:
        staff_member = _current_staff_member(db, current_user)
        allowed_salons = _staff_allowed_salons(db, staff_member)
        if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not allowed_salons:
            allowed_salons = {row.id for row in visible_salons}
        visible_salons = [row for row in visible_salons if row.id in allowed_salons]

    visible_salon_ids = [row.id for row in visible_salons]
    if salon_id is not None:
        _require_salon_access(db, current_user, salon_id)
        visible_salon_ids = [salon_id]
        visible_salons = [row for row in visible_salons if row.id == salon_id]
    elif aggregate != "all" and len(visible_salon_ids) > 1:
        visible_salon_ids = visible_salon_ids[:1]
        visible_salons = visible_salons[:1]

    if not visible_salon_ids:
        return BookingStatsResponse(
            salons=0,
            clients=0,
            appointments=0,
            planned_appointments=0,
            completed_appointments=0,
            available_staff=0,
        )

    date_range = _resolve_date_filter(date)
    appointments_query = db.query(Appointment).filter(
        Appointment.tenant_id == current_user.tenant_id,
        Appointment.salon_id.in_(visible_salon_ids),
    )
    if date_range is not None:
        range_start, range_end = date_range
        appointments_query = appointments_query.filter(Appointment.start_at >= range_start, Appointment.start_at <= range_end)
    appointments = appointments_query.all()
    clients_count = int(
        db.query(func.count(func.distinct(Appointment.client_id)))
        .filter(Appointment.tenant_id == current_user.tenant_id, Appointment.salon_id.in_(visible_salon_ids))
        .scalar()
        or 0
    )

    now = datetime.now()
    done_today_appointment_ids = set()
    revenue_today = 0.0
    if date_range is not None:
        range_start, range_end = date_range
        done_today_rows = (
            db.query(AppointmentPerformedLine.appointment_id)
            .filter(AppointmentPerformedLine.performed_at >= range_start, AppointmentPerformedLine.performed_at <= range_end)
            .all()
        )
        done_today_appointment_ids = {int(row[0]) for row in done_today_rows}
        if done_today_appointment_ids:
            revenue_today = float(
                db.query(func.coalesce(func.sum(Appointment.total_price_snapshot), 0))
                .filter(Appointment.id.in_(done_today_appointment_ids), Appointment.salon_id.in_(visible_salon_ids))
                .scalar()
                or 0
            )
    in_progress_count = sum(
        1
        for row in appointments
        if (row.status or "").lower() in {"started", "in_progress"} or (
            row.start_at <= now <= row.end_at and (row.status or "").lower() not in {"done", "cancelled", "completed"}
        )
    )
    completed_count = sum(
        1
        for row in appointments
        if (row.status or "").lower() in {"done", "completed"} and (
            not done_today_appointment_ids or row.id in done_today_appointment_ids
        )
    )

    return BookingStatsResponse(
        salons=len(visible_salon_ids),
        clients=clients_count,
        appointments=len(appointments),
        planned_appointments=sum(1 for row in appointments if row.status not in {"done", "cancelled", "COMPLETED", "CANCELLED"}),
        completed_appointments=completed_count,
        available_staff=_count_available_staff(db, visible_salon_ids),
        appointments_in_progress=in_progress_count,
        revenue_today=revenue_today,
    )


@router.get("/appointments", response_model=list[BookingAppointment])
async def list_appointments(
    salon_id: int | None = None,
    date: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    datefrom: datetime | None = Query(None, alias="datefrom"),
    dateto: datetime | None = Query(None, alias="dateto"),
    status_filter: str | None = Query(None, alias="status"),
    sort: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visible_salons = db.query(Salon).filter(Salon.tenant_id == current_user.tenant_id).all()
    if current_user.role != UserRole.ADMIN:
        staff_member = _current_staff_member(db, current_user)
        allowed_salons = _staff_allowed_salons(db, staff_member)
        if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not allowed_salons:
            allowed_salons = {row.id for row in visible_salons}
        visible_salons = [row for row in visible_salons if row.id in allowed_salons]

    visible_salon_ids = [row.id for row in visible_salons]
    if salon_id is not None:
        _require_salon_access(db, current_user, salon_id)
        visible_salon_ids = [salon_id]

    if not visible_salon_ids:
        return []

    query = db.query(Appointment).filter(
        Appointment.tenant_id == current_user.tenant_id,
        Appointment.salon_id.in_(visible_salon_ids),
    )
    if status_filter:
        requested_statuses = [value.strip().lower() for value in status_filter.split(",") if value.strip()]
        if requested_statuses:
            query = query.filter(func.lower(Appointment.status).in_(requested_statuses))
    effective_date_from = date_from or datefrom
    effective_date_to = date_to or dateto
    if effective_date_from is not None:
        query = query.filter(Appointment.start_at >= effective_date_from)
    if effective_date_to is not None:
        query = query.filter(Appointment.start_at <= effective_date_to)
    if effective_date_from is None and effective_date_to is None:
        date_range = _resolve_date_filter(date)
        if date_range is not None:
            range_start, range_end = date_range
        else:
            today = datetime.now().date()
            range_start = datetime.combine(today, time.min)
            range_end = datetime.combine(today + timedelta(days=1), time.max)
        query = query.filter(Appointment.start_at >= range_start, Appointment.start_at <= range_end)

    if sort == "start_asc":
        query = query.order_by(Appointment.start_at.asc())
    elif sort == "start_desc":
        query = query.order_by(Appointment.start_at.desc())
    else:
        query = query.order_by(Appointment.start_at.desc())

    appointments = query.limit(500).all()
    appointment_ids = [row.id for row in appointments]

    resources_by_appointment: dict[int, list[int]] = {}
    service_by_appointment: dict[int, list[int]] = {}
    if appointment_ids:
        resource_links = db.query(AppointmentResource).filter(AppointmentResource.appointment_id.in_(appointment_ids)).all()
        for link in resource_links:
            resources_by_appointment.setdefault(link.appointment_id, []).append(link.staff_id)
        service_links = db.query(AppointmentService).filter(AppointmentService.appointment_id.in_(appointment_ids)).all()
        for link in service_links:
            service_by_appointment.setdefault(link.appointment_id, []).append(link.service_id)

    return [_to_appointment(row, resources_by_appointment, service_by_appointment) for row in appointments]


@router.post("/clients", response_model=BookingClient, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: BookingClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user

    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="full_name is required")

    parts = full_name.split(maxsplit=1)
    customer = Customer(
        tenant_id=current_user.tenant_id,
        display_name=full_name,
        first_name=parts[0],
        last_name=parts[1] if len(parts) > 1 else None,
        phone=payload.phone.strip(),
        email=(payload.email or "").strip() or None,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _to_client(customer)


@router.patch("/clients/{client_id}", response_model=BookingClient)
async def update_client(
    client_id: int,
    payload: BookingClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(
        Customer.id == client_id,
        Customer.tenant_id == current_user.tenant_id,
    ).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    provided = payload.model_fields_set
    if "full_name" in provided and payload.full_name is not None:
        full_name = payload.full_name.strip()
        if not full_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="full_name is required")
        parts = full_name.split(maxsplit=1)
        customer.display_name = full_name
        customer.first_name = parts[0]
        customer.last_name = parts[1] if len(parts) > 1 else None
    if "phone" in provided and payload.phone is not None:
        phone = payload.phone.strip()
        if not phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="phone is required")
        customer.phone = phone
    if "email" in provided:
        customer.email = (payload.email or "").strip() or None

    db.commit()
    db.refresh(customer)
    return _to_client(customer)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(
        Customer.id == client_id,
        Customer.tenant_id == current_user.tenant_id,
    ).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    refs = {
        "appointments": db.query(Appointment.id).filter(
            Appointment.client_id == client_id,
            Appointment.tenant_id == current_user.tenant_id,
        ).count(),
        "payments": db.query(Payment.id).filter(Payment.client_id == client_id).count(),
        "sales": db.query(Sale.id).filter(Sale.customer_id == client_id, Sale.tenant_id == current_user.tenant_id).count(),
        "client_cards": db.query(ClientCard.id).filter(ClientCard.client_id == client_id).count(),
        "invitations": db.query(Invitation.id).filter(Invitation.client_id == client_id).count(),
    }
    if any(refs.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Nie mozna usunac klienta z powiazaniami: "
                + ", ".join(f"{name}={count}" for name, count in refs.items() if count > 0)
            ),
        )

    db.delete(customer)
    db.commit()
    return None


@router.post("/appointments", response_model=BookingAppointment, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: BookingAppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, payload.salon_id)

    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_at must be after start_at")
    _validate_not_backdated(payload.start_at)
    if payload.allow_overlap and current_user.role not in {
        UserRole.ADMIN,
        UserRole.MANAGER,
        UserRole.MANAGER_MAIN,
        UserRole.MANAGER_SALON,
        UserRole.RECEPTIONIST,
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to create overlap appointments")

    salon = db.query(Salon).filter(
        Salon.id == payload.salon_id,
        Salon.tenant_id == current_user.tenant_id,
    ).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    client = db.query(Customer).filter(
        Customer.id == payload.client_id,
        Customer.tenant_id == current_user.tenant_id,
    ).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if payload.bundle_id is not None:
        bundle = db.query(BundleCatalog).filter(BundleCatalog.id == payload.bundle_id).first()
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
        if (bundle.salon_id or payload.salon_id) != payload.salon_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bundle does not belong to salon")

    resource_ids = list(dict.fromkeys(payload.resources))
    if resource_ids:
        found_resources = (
            db.query(StaffMember.id)
            .filter(StaffMember.id.in_(resource_ids), StaffMember.salon_id == payload.salon_id)
            .all()
        )
        found_ids = {row[0] for row in found_resources}
        missing = [rid for rid in resource_ids if rid not in found_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Staff not found: {missing}")
        if payload.start_at.date() != payload.end_at.date():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment must start and end on the same day")
        for resource_id in resource_ids:
            work_windows = _staff_work_windows_for_day(
                db,
                staff_id=resource_id,
                salon_id=payload.salon_id,
                day=payload.start_at.date(),
            )
            in_schedule = any(
                payload.start_at >= window_start and payload.end_at <= window_end
                for window_start, window_end in work_windows
            )
            if not in_schedule:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Termin poza grafikiem pracy pracownika #{resource_id}",
                )

        if not payload.allow_overlap:
            conflict_exists = (
                db.query(Appointment.id)
                .join(AppointmentResource, AppointmentResource.appointment_id == Appointment.id)
                .filter(
                    Appointment.salon_id == payload.salon_id,
                    AppointmentResource.staff_id.in_(resource_ids),
                    Appointment.start_at < payload.end_at,
                    Appointment.end_at > payload.start_at,
                    Appointment.allow_overlap.is_(False),
                    Appointment.status.in_(["pending", "planned", "confirmed", "started", "in_progress"]),
                )
                .first()
            )
            if conflict_exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wybrany pracownik jest zajety w tym terminie")

    service_ids = list(dict.fromkeys(payload.services))
    if service_ids:
        found_services = db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id.in_(service_ids)).all()
        found_ids = {row[0] for row in found_services}
        missing = [sid for sid in service_ids if sid not in found_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service not found: {missing}")

    appointment = Appointment(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        client_id=payload.client_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status="planned",
        allow_overlap=bool(payload.allow_overlap),
        bundle_id=payload.bundle_id,
        total_price_snapshot=payload.total_price_snapshot,
    )
    db.add(appointment)
    db.flush()

    for resource_id in resource_ids:
        db.add(AppointmentResource(appointment_id=appointment.id, staff_id=resource_id))
    for service_id in service_ids:
        db.add(AppointmentService(appointment_id=appointment.id, service_id=service_id))

    db.commit()
    db.refresh(appointment)

    return _to_appointment(
        appointment,
        resources_by_appointment={appointment.id: resource_ids},
        services_by_appointment={appointment.id: service_ids},
    )


async def _perform_appointment(
    appointment_id: int,
    payload: BookingAppointmentComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.tenant_id == current_user.tenant_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    existing_line_ids = [
        row.id
        for row in db.query(AppointmentPerformedLine.id).filter(AppointmentPerformedLine.appointment_id == appointment_id).all()
    ]
    if existing_line_ids:
        db.query(PerformedLineResource).filter(PerformedLineResource.performedline_id.in_(existing_line_ids)).delete(
            synchronize_session=False,
        )
    db.query(AppointmentPerformedLine).filter(AppointmentPerformedLine.appointment_id == appointment_id).delete()

    total = 0.0
    for line in payload.lines:
        service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == line.service_id).first()
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service not found: {line.service_id}")
        if not db.query(StaffMember.id).filter(
            StaffMember.id == line.worker_id,
            StaffMember.tenant_id == current_user.tenant_id,
        ).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Worker not found: {line.worker_id}")
        if not db.query(StaffRole.id).filter(StaffRole.id == line.worker_role_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role not found: {line.worker_role_id}")
        if line.color_product_id is not None and not db.query(LegacyProductCatalogItem.id).filter(LegacyProductCatalogItem.id == line.color_product_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Color product not found: {line.color_product_id}")
        recipe_items = (
            db.query(ServiceRecipeItem)
            .filter(ServiceRecipeItem.service_id == line.service_id)
            .order_by(ServiceRecipeItem.position.asc(), ServiceRecipeItem.id.asc())
            .all()
        )
        recipe_by_id = {item.id: item for item in recipe_items}
        recipe_ids = set(recipe_by_id)
        required_recipe_ids = {
            item.id
            for item in recipe_items
            if bool(getattr(item, "is_required", True)) and (item.inventory_mode or "PER_SERVICE") == "PER_SERVICE"
        }
        payload_recipe_ids = [item.recipe_item_id for item in line.resources]
        payload_recipe_ids_set = set(payload_recipe_ids)
        if len(payload_recipe_ids) != len(payload_recipe_ids_set):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate recipe resources for service: {line.service_id}",
            )
        invalid_recipe_ids = payload_recipe_ids_set.difference(recipe_ids)
        if invalid_recipe_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid recipe resources for service: {line.service_id}",
            )
        missing_required = required_recipe_ids.difference(payload_recipe_ids_set)
        if missing_required:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required recipe resources for service: {line.service_id}",
            )
        products_by_id: dict[int, LegacyProductCatalogItem] = {}
        for resource in line.resources:
            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == resource.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recipe product not found: {resource.product_id}",
                )
            recipe_item = recipe_by_id[resource.recipe_item_id]
            if not _matches_recipe_family(recipe_item.product_family, product):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product does not match recipe family for recipe item: {resource.recipe_item_id}",
                )
            products_by_id[resource.product_id] = product

        performed_line = AppointmentPerformedLine(
            appointment_id=appointment_id,
            service_id=line.service_id,
            worker_id=line.worker_id,
            worker_role_id=line.worker_role_id,
            service_name_snapshot=service.name,
            list_price_snapshot=Decimal(str(service.default_price or 0)) if service.default_price is not None else Decimal(str(line.price_snapshot)),
            discount_allocated_snapshot=max(
                (Decimal(str(service.default_price or line.price_snapshot)) - Decimal(str(line.price_snapshot))),
                Decimal("0"),
            ),
            sold_as_bundle=appointment.bundle_id is not None,
            bundle_id_snapshot=appointment.bundle_id,
            price_snapshot=line.price_snapshot,
            performed_at=payload.performed_at,
            color_product_id=line.color_product_id or (line.resources[0].product_id if line.resources else None),
        )
        db.add(performed_line)
        db.flush()
        for resource in line.resources:
            recipe_item = recipe_by_id[resource.recipe_item_id]
            product = products_by_id[resource.product_id]
            quantity_used = Decimal(str(resource.quantity_used))
            quantity_unit = (
                (resource.quantity_unit or "").strip().upper()
                or (recipe_item.recipe_unit_label or recipe_item.unit or "").strip().upper()
                or "PCS"
            )
            unit_cost_snapshot = _estimate_product_unit_cost(product)
            db.add(
                PerformedLineResource(
                    performedline_id=performed_line.id,
                    recipeitem_id=resource.recipe_item_id,
                    product_id=resource.product_id,
                    product_family_snapshot=recipe_item.product_family or product.family_code,
                    product_name_snapshot=product.name,
                    quantity_used=quantity_used,
                    quantity_unit=quantity_unit,
                    unit_cost_snapshot=unit_cost_snapshot,
                    total_cost_snapshot=(quantity_used * unit_cost_snapshot),
                )
            )
        total += float(line.price_snapshot)

    appointment.status = "done"
    appointment.total_price_snapshot = total

    db.commit()
    db.refresh(appointment)

    resources = [
        row.staff_id
        for row in db.query(AppointmentResource).filter(AppointmentResource.appointment_id == appointment_id).all()
    ]
    services = [
        row.service_id
        for row in db.query(AppointmentService).filter(AppointmentService.appointment_id == appointment_id).all()
    ]
    return _to_appointment(
        appointment,
        resources_by_appointment={appointment.id: resources},
        services_by_appointment={appointment.id: services},
    )


@router.post("/appointments/{appointment_id}/complete", response_model=BookingAppointment)
async def complete_appointment(
    appointment_id: int,
    payload: BookingAppointmentComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _perform_appointment(appointment_id, payload, current_user, db)


@router.post("/appointments/{appointment_id}/perform", response_model=BookingAppointment)
async def perform_appointment(
    appointment_id: int,
    payload: BookingAppointmentComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _perform_appointment(appointment_id, payload, current_user, db)


def _appointment_payload(db: Session, appointment: Appointment) -> BookingAppointment:
    resources = [
        row.staff_id
        for row in db.query(AppointmentResource).filter(AppointmentResource.appointment_id == appointment.id).all()
    ]
    services = [
        row.service_id
        for row in db.query(AppointmentService).filter(AppointmentService.appointment_id == appointment.id).all()
    ]
    return _to_appointment(
        appointment,
        resources_by_appointment={appointment.id: resources},
        services_by_appointment={appointment.id: services},
    )


@router.post("/appointments/{appointment_id}/cancel", response_model=BookingAppointment)
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    normalized_status = (appointment.status or "").lower()
    if normalized_status in {"done", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed appointment cannot be cancelled")
    if normalized_status == "cancelled":
        return _appointment_payload(db, appointment)
    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)
    return _appointment_payload(db, appointment)


@router.post("/appointments/{appointment_id}/no-show", response_model=BookingAppointment)
async def mark_appointment_no_show(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    normalized_status = (appointment.status or "").lower()
    if normalized_status in {"done", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed appointment cannot be marked as no-show")
    if normalized_status == "no_show":
        return _appointment_payload(db, appointment)
    appointment.status = "no_show"
    db.commit()
    db.refresh(appointment)
    return _appointment_payload(db, appointment)


@router.post("/appointments/{appointment_id}/reopen", response_model=BookingAppointment)
async def reopen_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    normalized_status = (appointment.status or "").lower()
    if normalized_status in {"done", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed appointment cannot be reopened")
    if normalized_status in {"cancelled", "no_show", "rejected"}:
        appointment.status = "planned"
        db.commit()
        db.refresh(appointment)
    return _appointment_payload(db, appointment)


@router.post("/appointments/{appointment_id}/confirm", response_model=BookingAppointment)
async def confirm_pending_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to confirm public bookings")
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    if (appointment.status or "").lower() != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending appointments can be confirmed")
    appointment.status = "confirmed"
    db.commit()
    db.refresh(appointment)
    try:
        send_appointment_sms(db, appointment.id, notification_type="public_confirmed")
    except Exception:
        pass
    return _appointment_payload(db, appointment)


@router.post("/appointments/{appointment_id}/reject", response_model=BookingAppointment)
async def reject_pending_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to reject public bookings")
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    if (appointment.status or "").lower() != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending appointments can be rejected")
    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)
    try:
        send_appointment_sms(db, appointment.id, notification_type="public_rejected")
    except Exception:
        pass
    return _appointment_payload(db, appointment)


@router.post("/appointments/{appointment_id}/sms-notify", response_model=BookingSmsNotifyResponse)
async def sms_notify_appointment(
    appointment_id: int,
    payload: BookingSmsNotifyRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)
    try:
        notification = send_appointment_sms(
            db,
            appointment_id,
            notification_type="confirmation",
            override_phone=payload.phone if payload else None,
        )
    except ValueError as exc:
        detail_map = {
            "appointment_not_found": "Appointment not found",
            "customer_not_found": "Customer not found",
            "missing_phone": "Customer phone number is missing",
        }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail_map.get(str(exc), str(exc))) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return BookingSmsNotifyResponse(
        notification_id=notification.id,
        appointment_id=notification.appointment_id,
        phone=notification.phone,
        status=notification.status,
        notification_type=notification.notification_type,
        error_message=notification.error_message,
    )


@router.post("/appointments/sms-notify-today", response_model=BookingSmsBatchResponse)
async def sms_notify_today(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, salon_id)
    try:
        result = send_today_batch_sms(db, salon_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return BookingSmsBatchResponse(sent=result["sent"], failed=result["failed"])


@router.get("/appointments/{appointment_id}/performed-resources", response_model=list[BookingPerformedLineResourceRead])
async def list_performed_resources(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.tenant_id == current_user.tenant_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    _require_salon_access(db, current_user, appointment.salon_id)

    rows = (
        db.query(
            PerformedLineResource.performedline_id.label("performed_line_id"),
            AppointmentPerformedLine.service_id.label("service_id"),
            ServiceCatalogItem.name.label("service_name"),
            AppointmentPerformedLine.worker_id.label("worker_id"),
            StaffMember.first_name.label("worker_first_name"),
            StaffMember.last_name.label("worker_last_name"),
            AppointmentPerformedLine.worker_role_id.label("worker_role_id"),
            StaffRole.name.label("worker_role_name"),
            PerformedLineResource.product_id.label("product_id"),
            PerformedLineResource.product_family_snapshot.label("product_family"),
            PerformedLineResource.product_name_snapshot.label("product_name_snapshot"),
            LegacyProductCatalogItem.name.label("product_name_current"),
            PerformedLineResource.quantity_used.label("quantity_used"),
            PerformedLineResource.quantity_unit.label("quantity_unit"),
            PerformedLineResource.unit_cost_snapshot.label("unit_cost_snapshot"),
            PerformedLineResource.total_cost_snapshot.label("total_cost_snapshot"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .outerjoin(StaffMember, StaffMember.id == AppointmentPerformedLine.worker_id)
        .outerjoin(StaffRole, StaffRole.id == AppointmentPerformedLine.worker_role_id)
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
        .filter(AppointmentPerformedLine.appointment_id == appointment_id)
        .order_by(PerformedLineResource.performedline_id.asc(), PerformedLineResource.id.asc())
        .all()
    )

    return [
        BookingPerformedLineResourceRead(
            performed_line_id=int(row.performed_line_id),
            service_id=int(row.service_id),
            service_name=row.service_name,
            worker_id=int(row.worker_id),
            worker_name=f"{(row.worker_first_name or '').strip()} {(row.worker_last_name or '').strip()}".strip() or None,
            worker_role_id=int(row.worker_role_id),
            worker_role_name=row.worker_role_name,
            product_id=int(row.product_id),
            product_family=row.product_family,
            product_name=row.product_name_snapshot or row.product_name_current,
            quantity_used=float(row.quantity_used or 0),
            quantity_unit=row.quantity_unit,
            unit_cost_snapshot=float(row.unit_cost_snapshot) if row.unit_cost_snapshot is not None else None,
            total_cost_snapshot=float(row.total_cost_snapshot) if row.total_cost_snapshot is not None else None,
        )
        for row in rows
    ]


@router.get("/salons/{salon_id}/staff", response_model=list[BookingSalonStaffMember])
async def list_salon_staff(
    salon_id: int,
    can_take_bookings: bool | None = Query(default=None, alias="can_take_bookings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, salon_id)
    rows = _staff_in_salon(db, salon_id, current_user.tenant_id)
    if can_take_bookings is not None:
        rows = [row for row in rows if bool(row.can_be_booked) is bool(can_take_bookings)]
    return [_to_salon_staff_member(db, row) for row in rows]


@router.get("/staff/{staff_id}/locations", response_model=list[BookingStaffLocationRead])
async def get_staff_locations(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)

    salons_by_id = {row.id: row for row in db.query(Salon).all()}
    rows: list[BookingStaffLocationRead] = []
    seen: set[int] = set()
    if staff.salon_id is not None:
        primary_salon = salons_by_id.get(staff.salon_id)
        rows.append(
            BookingStaffLocationRead(
                salon_id=staff.salon_id,
                salon_name=primary_salon.name if primary_salon else None,
                is_primary=True,
                is_active=bool(staff.is_active),
            )
        )
        seen.add(staff.salon_id)

    memberships = (
        db.query(StaffSalonMembership)
        .filter(StaffSalonMembership.staff_id == staff_id)
        .order_by(StaffSalonMembership.salon_id.asc())
        .all()
    )
    for item in memberships:
        if item.salon_id in seen:
            continue
        salon = salons_by_id.get(item.salon_id)
        rows.append(
            BookingStaffLocationRead(
                salon_id=item.salon_id,
                salon_name=salon.name if salon else None,
                is_primary=bool(item.is_primary),
                is_active=bool(item.is_active),
            )
        )
    return rows


@router.post("/staff/{staff_id}/locations", response_model=list[BookingStaffLocationRead], status_code=status.HTTP_201_CREATED)
async def add_staff_location(
    staff_id: int,
    payload: BookingStaffLocationWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    if not db.query(Salon.id).filter(Salon.id == payload.salon_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    _require_staff_access(db, current_user, staff)
    _require_salon_access(db, current_user, payload.salon_id)

    existing = (
        db.query(StaffSalonMembership)
        .filter(
            StaffSalonMembership.staff_id == staff_id,
            StaffSalonMembership.salon_id == payload.salon_id,
        )
        .first()
    )
    if existing:
        existing.is_active = True
        existing.is_primary = payload.is_primary
    else:
        db.add(
            StaffSalonMembership(
                staff_id=staff_id,
                salon_id=payload.salon_id,
                is_primary=payload.is_primary,
                is_active=True,
            )
        )

    if payload.is_primary:
        db.query(StaffSalonMembership).filter(
            StaffSalonMembership.staff_id == staff_id,
            StaffSalonMembership.salon_id != payload.salon_id,
        ).update({StaffSalonMembership.is_primary: False})
        staff.salon_id = payload.salon_id

    db.commit()
    return await get_staff_locations(staff_id=staff_id, current_user=current_user, db=db)


@router.delete("/staff/{staff_id}/locations", response_model=list[BookingStaffLocationRead])
async def remove_staff_location(
    staff_id: int,
    salon_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    _require_salon_access(db, current_user, salon_id)

    if staff.salon_id == salon_id:
        staff.salon_id = None

    membership = (
        db.query(StaffSalonMembership)
        .filter(
            StaffSalonMembership.staff_id == staff_id,
            StaffSalonMembership.salon_id == salon_id,
        )
        .first()
    )
    if membership:
        db.delete(membership)
    db.commit()
    return await get_staff_locations(staff_id=staff_id, current_user=current_user, db=db)


@router.get("/staff/{staff_id}/bundle-offers", response_model=list[BookingStaffBundleOfferRead])
async def get_staff_bundle_offers(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id, StaffMember.tenant_id == current_user.tenant_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    rows = (
        db.query(StaffBundleOffer, BundleCatalog)
        .join(BundleCatalog, BundleCatalog.id == StaffBundleOffer.bundle_id)
        .filter(
            StaffBundleOffer.tenant_id == current_user.tenant_id,
            StaffBundleOffer.staff_id == staff_id,
        )
        .order_by(StaffBundleOffer.priority.asc(), BundleCatalog.name.asc())
        .all()
    )
    return [
        BookingStaffBundleOfferRead(
            staff_id=staff_id,
            bundle_id=offer.bundle_id,
            bundle_code=bundle.legacy_code,
            bundle_name=bundle.name,
            priority=int(offer.priority or 100),
            is_active=bool(offer.is_active),
        )
        for offer, bundle in rows
    ]


@router.put("/staff/{staff_id}/bundle-offers", response_model=list[BookingStaffBundleOfferRead])
async def set_staff_bundle_offers(
    staff_id: int,
    payload: BookingStaffBundleOfferWrite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id, StaffMember.tenant_id == current_user.tenant_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to edit staff bundle offers")
    if staff.salon_id is None and payload.offers:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff has no primary salon assigned")

    desired_by_bundle = {int(item.bundle_id): item for item in payload.offers}
    if desired_by_bundle:
        existing_bundle_ids = {
            row[0]
            for row in db.query(BundleCatalog.id).filter(
                BundleCatalog.salon_id == staff.salon_id,
                BundleCatalog.id.in_(list(desired_by_bundle.keys())),
            ).all()
        }
        missing = [bundle_id for bundle_id in desired_by_bundle if bundle_id not in existing_bundle_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bundle not found in staff salon: {missing[0]}")

    existing_rows = (
        db.query(StaffBundleOffer)
        .filter(
            StaffBundleOffer.tenant_id == current_user.tenant_id,
            StaffBundleOffer.staff_id == staff_id,
        )
        .all()
    )
    existing_by_bundle = {int(row.bundle_id): row for row in existing_rows}

    for bundle_id, item in desired_by_bundle.items():
        row = existing_by_bundle.get(bundle_id)
        if row is None:
            row = StaffBundleOffer(
                tenant_id=current_user.tenant_id,
                salon_id=staff.salon_id,
                staff_id=staff_id,
                bundle_id=bundle_id,
            )
            db.add(row)
        row.priority = int(item.priority or 100)
        row.is_active = bool(item.is_active)
        row.salon_id = staff.salon_id or row.salon_id
        row.updated_at = func.now()

    for bundle_id, row in existing_by_bundle.items():
        if bundle_id not in desired_by_bundle:
            row.is_active = False
            row.updated_at = func.now()

    db.commit()
    return await get_staff_bundle_offers(staff_id=staff_id, current_user=current_user, db=db)


@router.get("/staff/{staff_id}/schedule", response_model=list[BookingStaffWeeklyScheduleRead])
async def get_staff_schedule(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    rows = (
        db.query(StaffWeeklySchedule)
        .filter(StaffWeeklySchedule.staff_id == staff_id)
        .order_by(StaffWeeklySchedule.weekday.asc(), StaffWeeklySchedule.time_from.asc())
        .all()
    )
    return [
        BookingStaffWeeklyScheduleRead(
            id=row.id,
            staff_id=row.staff_id,
            salon_id=row.salon_id,
            weekday=row.weekday,
            time_from=row.time_from,
            time_to=row.time_to,
            is_active=bool(row.is_active),
        )
        for row in rows
    ]


@router.post("/staff/{staff_id}/schedule", response_model=BookingStaffWeeklyScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_staff_schedule(
    staff_id: int,
    payload: BookingStaffWeeklyScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, payload.salon_id)
    if payload.time_to <= payload.time_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="time_to must be after time_from")
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    row = StaffWeeklySchedule(
        staff_id=staff_id,
        salon_id=payload.salon_id,
        weekday=payload.weekday,
        time_from=payload.time_from,
        time_to=payload.time_to,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return BookingStaffWeeklyScheduleRead(
        id=row.id,
        staff_id=row.staff_id,
        salon_id=row.salon_id,
        weekday=row.weekday,
        time_from=row.time_from,
        time_to=row.time_to,
        is_active=bool(row.is_active),
    )


@router.patch("/staff/{staff_id}/schedule/{schedule_id}", response_model=BookingStaffWeeklyScheduleRead)
async def update_staff_schedule(
    staff_id: int,
    schedule_id: int,
    payload: BookingStaffWeeklyScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(StaffWeeklySchedule)
        .filter(StaffWeeklySchedule.id == schedule_id, StaffWeeklySchedule.staff_id == staff_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    _require_salon_access(db, current_user, row.salon_id)

    if payload.salon_id is not None:
        _require_salon_access(db, current_user, payload.salon_id)
        row.salon_id = payload.salon_id
    if payload.weekday is not None:
        row.weekday = payload.weekday
    if payload.time_from is not None:
        row.time_from = payload.time_from
    if payload.time_to is not None:
        row.time_to = payload.time_to
    if payload.is_active is not None:
        row.is_active = payload.is_active
    if row.time_to <= row.time_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="time_to must be after time_from")

    db.commit()
    db.refresh(row)
    return BookingStaffWeeklyScheduleRead(
        id=row.id,
        staff_id=row.staff_id,
        salon_id=row.salon_id,
        weekday=row.weekday,
        time_from=row.time_from,
        time_to=row.time_to,
        is_active=bool(row.is_active),
    )


@router.delete("/staff/{staff_id}/schedule/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_schedule(
    staff_id: int,
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(StaffWeeklySchedule)
        .filter(StaffWeeklySchedule.id == schedule_id, StaffWeeklySchedule.staff_id == staff_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    _require_salon_access(db, current_user, row.salon_id)
    db.delete(row)
    db.commit()


@router.get("/staff/{staff_id}/monthly-schedule", response_model=list[BookingStaffMonthlyScheduleRead])
async def get_staff_monthly_schedule(
    staff_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if date_to < date_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to must be on or after date_from")
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    rows = (
        db.query(StaffMonthlySchedule)
        .filter(
            StaffMonthlySchedule.staff_id == staff_id,
            StaffMonthlySchedule.work_date >= date_from,
            StaffMonthlySchedule.work_date <= date_to,
        )
        .order_by(StaffMonthlySchedule.work_date.asc(), StaffMonthlySchedule.time_from.asc())
        .all()
    )
    return [
        BookingStaffMonthlyScheduleRead(
            id=row.id,
            staff_id=row.staff_id,
            salon_id=row.salon_id,
            work_date=row.work_date,
            time_from=row.time_from,
            time_to=row.time_to,
            is_active=bool(row.is_active),
        )
        for row in rows
    ]


@router.put("/staff/{staff_id}/monthly-schedule", response_model=list[BookingStaffMonthlyScheduleRead])
async def replace_staff_monthly_schedule(
    staff_id: int,
    payload: BookingStaffMonthlyScheduleReplace,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.date_to < payload.date_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to must be on or after date_from")

    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)

    for entry in payload.entries:
        if entry.work_date < payload.date_from or entry.work_date > payload.date_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry date is outside selected range")
        if entry.time_to <= entry.time_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="time_to must be after time_from")
        _require_salon_access(db, current_user, entry.salon_id)

    (
        db.query(StaffMonthlySchedule)
        .filter(
            StaffMonthlySchedule.staff_id == staff_id,
            StaffMonthlySchedule.work_date >= payload.date_from,
            StaffMonthlySchedule.work_date <= payload.date_to,
        )
        .delete(synchronize_session=False)
    )

    for entry in payload.entries:
        db.add(
            StaffMonthlySchedule(
                staff_id=staff_id,
                salon_id=entry.salon_id,
                work_date=entry.work_date,
                time_from=entry.time_from,
                time_to=entry.time_to,
                is_active=bool(entry.is_active),
            )
        )

    db.commit()
    rows = (
        db.query(StaffMonthlySchedule)
        .filter(
            StaffMonthlySchedule.staff_id == staff_id,
            StaffMonthlySchedule.work_date >= payload.date_from,
            StaffMonthlySchedule.work_date <= payload.date_to,
        )
        .order_by(StaffMonthlySchedule.work_date.asc(), StaffMonthlySchedule.time_from.asc())
        .all()
    )
    return [
        BookingStaffMonthlyScheduleRead(
            id=row.id,
            staff_id=row.staff_id,
            salon_id=row.salon_id,
            work_date=row.work_date,
            time_from=row.time_from,
            time_to=row.time_to,
            is_active=bool(row.is_active),
        )
        for row in rows
    ]


@router.get("/staff/{staff_id}/time-off", response_model=list[BookingStaffTimeOffRead])
async def get_staff_time_off(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    rows = (
        db.query(StaffTimeOff)
        .filter(StaffTimeOff.staff_id == staff_id)
        .order_by(StaffTimeOff.start_datetime.asc())
        .all()
    )
    return [
        BookingStaffTimeOffRead(
            id=row.id,
            staff_id=row.staff_id,
            salon_id=row.salon_id,
            start_datetime=row.start_datetime,
            end_datetime=row.end_datetime,
            reason=row.reason,
        )
        for row in rows
    ]


@router.post("/staff/{staff_id}/time-off", response_model=BookingStaffTimeOffRead, status_code=status.HTTP_201_CREATED)
async def create_staff_time_off(
    staff_id: int,
    payload: BookingStaffTimeOffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, payload.salon_id)
    if payload.end_datetime <= payload.start_datetime:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_datetime must be after start_datetime")
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    _require_staff_access(db, current_user, staff)
    row = StaffTimeOff(
        staff_id=staff_id,
        salon_id=payload.salon_id,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        reason=payload.reason,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return BookingStaffTimeOffRead(
        id=row.id,
        staff_id=row.staff_id,
        salon_id=row.salon_id,
        start_datetime=row.start_datetime,
        end_datetime=row.end_datetime,
        reason=row.reason,
    )


@router.patch("/staff/{staff_id}/time-off/{time_off_id}", response_model=BookingStaffTimeOffRead)
async def update_staff_time_off(
    staff_id: int,
    time_off_id: int,
    payload: BookingStaffTimeOffUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(StaffTimeOff)
        .filter(StaffTimeOff.id == time_off_id, StaffTimeOff.staff_id == staff_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time off not found")
    _require_salon_access(db, current_user, row.salon_id)

    if payload.salon_id is not None:
        _require_salon_access(db, current_user, payload.salon_id)
        row.salon_id = payload.salon_id
    if payload.start_datetime is not None:
        row.start_datetime = payload.start_datetime
    if payload.end_datetime is not None:
        row.end_datetime = payload.end_datetime
    if payload.reason is not None:
        row.reason = payload.reason
    if row.end_datetime <= row.start_datetime:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_datetime must be after start_datetime")

    db.commit()
    db.refresh(row)
    return BookingStaffTimeOffRead(
        id=row.id,
        staff_id=row.staff_id,
        salon_id=row.salon_id,
        start_datetime=row.start_datetime,
        end_datetime=row.end_datetime,
        reason=row.reason,
    )


@router.delete("/staff/{staff_id}/time-off/{time_off_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_time_off(
    staff_id: int,
    time_off_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(StaffTimeOff)
        .filter(StaffTimeOff.id == time_off_id, StaffTimeOff.staff_id == staff_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time off not found")
    _require_salon_access(db, current_user, row.salon_id)
    db.delete(row)
    db.commit()


@router.get("/salons/{salon_id}/availability", response_model=BookingAvailabilityResponse)
async def get_salon_availability(
    salon_id: int,
    date_value: date = Query(..., alias="date"),
    service_ids: str | None = None,
    bundle_id: int | None = None,
    preferred_staff_id: int | None = None,
    slot_minutes: int = 15,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_salon_access(db, current_user, salon_id)
    if slot_minutes < 5 or slot_minutes > 120:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slot_minutes out of range")

    parsed_service_ids: list[int] = []
    if service_ids:
        try:
            parsed_service_ids = [int(value.strip()) for value in service_ids.split(",") if value.strip()]
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="service_ids must be comma-separated integers") from exc
    all_service_ids = _load_service_ids_for_duration(db, parsed_service_ids, bundle_id, salon_id)
    total_duration = _calc_total_duration(db, all_service_ids)

    hairdresser_roles = db.query(StaffRole.id).filter(func.lower(StaffRole.code) == "hairdresser").all()
    hairdresser_role_ids = {int(row[0]) for row in hairdresser_roles}

    staff_candidates = _staff_in_salon(db, salon_id, current_user.tenant_id)
    staff_candidates = [
        row for row in staff_candidates
        if row.can_be_booked and (not hairdresser_role_ids or row.role_id in hairdresser_role_ids)
    ]

    if preferred_staff_id is not None:
        staff_candidates = [row for row in staff_candidates if row.id == preferred_staff_id]
        if not staff_candidates:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferred staff not available in salon")

    day_start = datetime.combine(date_value, time.min)
    day_end = datetime.combine(date_value, time.max)

    appointments = (
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
    busy_by_staff: dict[int, list[tuple[datetime, datetime]]] = {}
    for staff_id, start_at, end_at in appointments:
        busy_by_staff.setdefault(int(staff_id), []).append((start_at, end_at))

    step_rows = (
        db.query(
            AppointmentServiceStep.staff_id,
            AppointmentServiceStep.start_time,
            AppointmentServiceStep.end_time,
            AppointmentServiceStep.planned_start,
            Appointment.start_at,
            Appointment.end_at,
        )
        .join(Appointment, Appointment.id == AppointmentServiceStep.appointment_id)
        .filter(
            Appointment.salon_id == salon_id,
            AppointmentServiceStep.staff_id.isnot(None),
            Appointment.start_at < day_end,
            Appointment.end_at > day_start,
            Appointment.allow_overlap.is_(False),
            AppointmentServiceStep.status.in_(["planned", "in_progress", "completed"]),
        )
        .all()
    )
    for staff_id, start_time, end_time, planned_start, appointment_start, appointment_end in step_rows:
        interval_start = start_time or planned_start or appointment_start
        interval_end = end_time or appointment_end
        if interval_start is None or interval_end is None:
            continue
        busy_by_staff.setdefault(int(staff_id), []).append((interval_start, interval_end))

    results: list[BookingAvailabilityStaffSlots] = []
    for staff in staff_candidates:
        day_slots: list[tuple[datetime, datetime]] = []
        monthly_schedules = (
            db.query(StaffMonthlySchedule)
            .filter(
                StaffMonthlySchedule.staff_id == staff.id,
                StaffMonthlySchedule.salon_id == salon_id,
                StaffMonthlySchedule.work_date == date_value,
                StaffMonthlySchedule.is_active.is_(True),
            )
            .order_by(StaffMonthlySchedule.time_from.asc())
            .all()
        )
        if monthly_schedules:
            for schedule in monthly_schedules:
                day_slots.append(
                    (
                        datetime.combine(date_value, schedule.time_from),
                        datetime.combine(date_value, schedule.time_to),
                    )
                )
        else:
            weekday = date_value.weekday()
            schedules = (
            db.query(StaffWeeklySchedule)
            .filter(
                StaffWeeklySchedule.staff_id == staff.id,
                StaffWeeklySchedule.salon_id == salon_id,
                StaffWeeklySchedule.weekday == weekday,
                StaffWeeklySchedule.is_active.is_(True),
            )
            .order_by(StaffWeeklySchedule.time_from.asc())
            .all()
            )
            for schedule in schedules:
                day_slots.append(
                    (
                        datetime.combine(date_value, schedule.time_from),
                        datetime.combine(date_value, schedule.time_to),
                    )
                )

        time_off_rows = (
            db.query(StaffTimeOff)
            .filter(
                StaffTimeOff.staff_id == staff.id,
                StaffTimeOff.salon_id == salon_id,
                StaffTimeOff.start_datetime < day_end,
                StaffTimeOff.end_datetime > day_start,
            )
            .all()
        )
        for row in time_off_rows:
            day_slots = _subtract_interval(day_slots, row.start_datetime, row.end_datetime)

        busy = busy_by_staff.get(staff.id, [])
        for bstart, bend in busy:
            day_slots = _subtract_interval(day_slots, bstart, bend)

        available_slots: list[BookingAvailabilitySlot] = []
        for slot_start, slot_end in day_slots:
            cursor = slot_start
            while cursor + timedelta(minutes=total_duration) <= slot_end:
                candidate_end = cursor + timedelta(minutes=total_duration)
                if not _has_conflict(cursor, candidate_end, busy):
                    available_slots.append(BookingAvailabilitySlot(start_at=cursor, end_at=candidate_end))
                cursor = cursor + timedelta(minutes=slot_minutes)

        results.append(
            BookingAvailabilityStaffSlots(
                staff_id=staff.id,
                staff_name=_normalize_staff_full_name(staff),
                slots=available_slots,
            )
        )

    return BookingAvailabilityResponse(
        salon_id=salon_id,
        date=date_value,
        total_duration_minutes=total_duration,
        service_ids=all_service_ids,
        preferred_staff_id=preferred_staff_id,
        results=results,
    )
