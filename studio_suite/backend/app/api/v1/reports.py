"""Operational reports API (read-only)."""
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    AppointmentPerformedLine,
    InventoryIssue,
    InventoryIssueLine,
    Sale,
    SaleLine,
    Salon,
    ServiceCatalogItem,
    StaffMember,
)
from app.models.user import User, UserRole
from app.schemas.reports import (
    MaterialDeviationByStaffResponse,
    MaterialDeviationByStaffRow,
    MaterialCostByServiceResponse,
    MaterialCostByServiceRow,
    MaterialUsageByStaffResponse,
    MaterialUsageByStaffRow,
    SalesBySalonResponse,
    SalesBySalonRow,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _apply_date_range(query, column, date_from: date | None, date_to: date | None):
    if date_from is not None:
        query = query.filter(column >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.filter(column <= datetime.combine(date_to, time.max))
    return query


def _allowed_salons_for_user(db: Session, current_user: User, current_staff: StaffMember | None) -> set[int] | None:
    if current_user.role == UserRole.ADMIN:
        return None
    allowed = get_staff_allowed_salons(db, current_staff)
    if current_user.role == UserRole.MANAGER and not allowed:
        return None
    return allowed


def _apply_salon_scope(query, salon_column, salon_id: int | None, db: Session, current_user: User, current_staff: StaffMember | None):
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        return query.filter(salon_column == salon_id)
    if allowed is not None:
        if not allowed:
            return query.filter(False)
        return query.filter(salon_column.in_(allowed))
    return query


@router.get("/material-usage/by-staff", response_model=MaterialUsageByStaffResponse)
async def material_usage_by_staff(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    only_me: bool = False,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            InventoryIssue.staff_id.label("staff_id"),
            StaffMember.display_name.label("staff_name"),
            func.count(func.distinct(InventoryIssue.id)).label("services_count"),
            func.count(InventoryIssueLine.id).label("lines_count"),
            func.coalesce(func.sum(InventoryIssueLine.quantity_actual), 0).label("total_quantity"),
            func.coalesce(func.sum(InventoryIssueLine.total_cost), 0).label("total_cost"),
        )
        .join(InventoryIssueLine, InventoryIssueLine.inventory_issue_id == InventoryIssue.id)
        .outerjoin(StaffMember, StaffMember.id == InventoryIssue.staff_id)
        .outerjoin(AppointmentPerformedLine, AppointmentPerformedLine.id == InventoryIssueLine.performed_line_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == func.coalesce(InventoryIssueLine.service_id, AppointmentPerformedLine.service_id))
    )

    query = _apply_salon_scope(query, InventoryIssue.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, InventoryIssue.issue_time, date_from, date_to)

    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(InventoryIssue.staff_id == current_staff.id)
    elif only_me:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is not linked with staff profile")
        query = query.filter(InventoryIssue.staff_id == current_staff.id)

    rows = (
        query.group_by(InventoryIssue.staff_id, StaffMember.display_name)
        .order_by(func.coalesce(func.sum(InventoryIssueLine.total_cost), 0).desc())
        .all()
    )

    return MaterialUsageByStaffResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            MaterialUsageByStaffRow(
                staff_id=row.staff_id,
                staff_name=row.staff_name,
                services_count=int(row.services_count or 0),
                lines_count=int(row.lines_count or 0),
                total_quantity=float(row.total_quantity or 0),
                total_cost=float(row.total_cost or 0),
            )
            for row in rows
        ],
    )


@router.get("/material-cost/by-service", response_model=MaterialCostByServiceResponse)
async def material_cost_by_service(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            func.coalesce(InventoryIssueLine.service_id, AppointmentPerformedLine.service_id).label("service_id"),
            ServiceCatalogItem.name.label("service_name"),
            func.count(InventoryIssueLine.id).label("lines_count"),
            func.coalesce(func.sum(InventoryIssueLine.quantity_actual), 0).label("total_quantity"),
            func.coalesce(func.sum(InventoryIssueLine.total_cost), 0).label("total_cost"),
        )
        .join(InventoryIssue, InventoryIssue.id == InventoryIssueLine.inventory_issue_id)
        .outerjoin(AppointmentPerformedLine, AppointmentPerformedLine.id == InventoryIssueLine.performed_line_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == func.coalesce(InventoryIssueLine.service_id, AppointmentPerformedLine.service_id))
    )

    query = _apply_salon_scope(query, InventoryIssue.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, InventoryIssue.issue_time, date_from, date_to)

    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(InventoryIssue.staff_id == current_staff.id)

    rows = (
        query.group_by(func.coalesce(InventoryIssueLine.service_id, AppointmentPerformedLine.service_id), ServiceCatalogItem.name)
        .order_by(func.coalesce(func.sum(InventoryIssueLine.total_cost), 0).desc())
        .all()
    )

    return MaterialCostByServiceResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            MaterialCostByServiceRow(
                service_id=row.service_id,
                service_name=row.service_name,
                lines_count=int(row.lines_count or 0),
                total_quantity=float(row.total_quantity or 0),
                total_cost=float(row.total_cost or 0),
            )
            for row in rows
        ],
    )


@router.get("/deviation/by-staff", response_model=MaterialDeviationByStaffResponse)
async def deviation_by_staff(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            InventoryIssue.staff_id.label("staff_id"),
            StaffMember.display_name.label("staff_name"),
            func.count(InventoryIssueLine.id).label("lines_count"),
            func.coalesce(func.sum(InventoryIssueLine.quantity_planned), 0).label("total_planned"),
            func.coalesce(func.sum(InventoryIssueLine.quantity_actual), 0).label("total_actual"),
        )
        .join(InventoryIssue, InventoryIssue.id == InventoryIssueLine.inventory_issue_id)
        .outerjoin(StaffMember, StaffMember.id == InventoryIssue.staff_id)
    )

    query = _apply_salon_scope(query, InventoryIssue.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, InventoryIssue.issue_time, date_from, date_to)

    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(InventoryIssue.staff_id == current_staff.id)

    rows = (
        query.group_by(InventoryIssue.staff_id, StaffMember.display_name)
        .order_by((func.coalesce(func.sum(InventoryIssueLine.quantity_actual), 0) - func.coalesce(func.sum(InventoryIssueLine.quantity_planned), 0)).desc())
        .all()
    )

    return MaterialDeviationByStaffResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            MaterialDeviationByStaffRow(
                staff_id=row.staff_id,
                staff_name=row.staff_name,
                lines_count=int(row.lines_count or 0),
                total_planned=float(row.total_planned or 0),
                total_actual=float(row.total_actual or 0),
                deviation=float((row.total_actual or 0) - (row.total_planned or 0)),
            )
            for row in rows
        ],
    )


@router.get("/sales/by-salon", response_model=SalesBySalonResponse)
async def sales_by_salon(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    query = (
        db.query(
            Sale.salon_id.label("salon_id"),
            Salon.name.label("salon_name"),
            func.count(func.distinct(Sale.id)).label("sales_count"),
            func.count(SaleLine.id).label("lines_count"),
            func.coalesce(func.sum(SaleLine.total_price_gross), 0).label("total_gross"),
        )
        .join(SaleLine, SaleLine.sale_id == Sale.id)
        .outerjoin(Salon, Salon.id == Sale.salon_id)
    )

    query = _apply_salon_scope(query, Sale.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, Sale.sale_time, date_from, date_to)

    rows = (
        query.group_by(Sale.salon_id, Salon.name)
        .order_by(func.coalesce(func.sum(SaleLine.total_price_gross), 0).desc())
        .all()
    )

    return SalesBySalonResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            SalesBySalonRow(
                salon_id=int(row.salon_id),
                salon_name=row.salon_name,
                sales_count=int(row.sales_count or 0),
                transactions_count=int(row.sales_count or 0),
                lines_count=int(row.lines_count or 0),
                total_gross=float(row.total_gross or 0),
            )
            for row in rows
        ],
    )
