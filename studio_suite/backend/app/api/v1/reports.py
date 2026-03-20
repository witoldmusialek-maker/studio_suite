"""Operational reports API (read-only)."""
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    BundleCatalog,
    Customer,
    InventoryIssue,
    InventoryIssueLine,
    LegacyProductCatalogItem,
    Payment,
    PaymentAllocation,
    PerformedLineResource,
    Sale,
    SaleLine,
    Salon,
    ServiceCatalogItem,
    ServiceRecipeItem,
    StaffMember,
)
from app.models.user import User, UserRole
from app.schemas.reports import (
    MaterialDeviationByStaffResponse,
    MaterialDeviationByStaffRow,
    MaterialCostByServiceResponse,
    MaterialCostByServiceRow,
    MaterialUsageByFamilyResponse,
    MaterialUsageByFamilyRow,
    BundleMarginResponse,
    BundleMarginRow,
    MaterialUsageByStaffResponse,
    MaterialUsageByStaffRow,
    PaymentsReportResponse,
    PaymentsReportRow,
    SalesBySalonResponse,
    SalesBySalonRow,
    RecipeDeviationByServiceResponse,
    RecipeDeviationByServiceRow,
    ServiceDemandResponse,
    ServiceDemandRow,
    ServiceMarginResponse,
    ServiceMarginRow,
    StaffPerformanceResponse,
    StaffPerformanceRow,
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
    if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and not allowed:
        return None
    return allowed


def _apply_salon_scope(query, salon_column, salon_id: int | None, db: Session, current_user: User, current_staff: StaffMember | None):
    query = query.filter(Appointment.tenant_id == current_user.tenant_id)
    allowed = _allowed_salons_for_user(db, current_user, current_staff)
    if salon_id is not None:
        require_salon_access(db, current_user, salon_id)
        return query.filter(salon_column == salon_id)
    if allowed is not None:
        if not allowed:
            return query.filter(False)
        return query.filter(salon_column.in_(allowed))
    return query


def _performed_line_costs_subquery():
    return (
        func
        .coalesce(
            func.sum(
                func.coalesce(
                    PerformedLineResource.total_cost_snapshot,
                    PerformedLineResource.quantity_used
                    * func.coalesce(
                        PerformedLineResource.unit_cost_snapshot,
                        LegacyProductCatalogItem.purchase_price,
                        LegacyProductCatalogItem.purchase_price_c,
                        LegacyProductCatalogItem.catalog_net_price,
                        0,
                    ),
                )
            ),
            0,
        )
    )


def _recipe_planned_quantity_expr():
    return func.coalesce(
        ServiceRecipeItem.planned_default,
        ServiceRecipeItem.planned_quantity,
        0,
    )


@router.get("/material-usage/by-staff", response_model=MaterialUsageByStaffResponse)
async def material_usage_by_staff(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from_date"),
    to_date: date | None = Query(default=None, alias="to_date"),
    only_me: bool = False,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    effective_date_from = date_from or from_date
    effective_date_to = date_to or to_date
    unit_cost_expr = func.coalesce(
        PerformedLineResource.unit_cost_snapshot,
        LegacyProductCatalogItem.purchase_price,
        LegacyProductCatalogItem.purchase_price_c,
        LegacyProductCatalogItem.catalog_net_price,
        0,
    )
    total_cost_expr = func.coalesce(
        PerformedLineResource.total_cost_snapshot,
        PerformedLineResource.quantity_used * unit_cost_expr,
        0,
    )
    query = (
        db.query(
            AppointmentPerformedLine.worker_id.label("staff_id"),
            StaffMember.display_name.label("staff_name"),
            func.count(func.distinct(AppointmentPerformedLine.id)).label("services_count"),
            func.count(PerformedLineResource.id).label("lines_count"),
            func.coalesce(func.sum(PerformedLineResource.quantity_used), 0).label("total_quantity"),
            func.coalesce(func.sum(total_cost_expr), 0).label("total_cost"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(StaffMember, StaffMember.id == AppointmentPerformedLine.worker_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
    )

    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, effective_date_from, effective_date_to)

    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(AppointmentPerformedLine.worker_id == current_staff.id)
    elif only_me:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is not linked with staff profile")
        query = query.filter(AppointmentPerformedLine.worker_id == current_staff.id)

    rows = (
        query.group_by(AppointmentPerformedLine.worker_id, StaffMember.display_name)
        .order_by(func.coalesce(func.sum(total_cost_expr), 0).desc())
        .all()
    )

    return MaterialUsageByStaffResponse(
        salon_id=salon_id,
        date_from=effective_date_from,
        date_to=effective_date_to,
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
    from_date: date | None = Query(default=None, alias="from_date"),
    to_date: date | None = Query(default=None, alias="to_date"),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    effective_date_from = date_from or from_date
    effective_date_to = date_to or to_date
    unit_cost_expr = func.coalesce(
        PerformedLineResource.unit_cost_snapshot,
        LegacyProductCatalogItem.purchase_price,
        LegacyProductCatalogItem.purchase_price_c,
        LegacyProductCatalogItem.catalog_net_price,
        0,
    )
    total_cost_expr = func.coalesce(
        PerformedLineResource.total_cost_snapshot,
        PerformedLineResource.quantity_used * unit_cost_expr,
        0,
    )
    query = (
        db.query(
            AppointmentPerformedLine.service_id.label("service_id"),
            ServiceCatalogItem.name.label("service_name"),
            func.count(PerformedLineResource.id).label("lines_count"),
            func.coalesce(func.sum(PerformedLineResource.quantity_used), 0).label("total_quantity"),
            func.coalesce(func.sum(total_cost_expr), 0).label("total_cost"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
    )

    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, effective_date_from, effective_date_to)

    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(AppointmentPerformedLine.worker_id == current_staff.id)

    rows = (
        query.group_by(AppointmentPerformedLine.service_id, ServiceCatalogItem.name)
        .order_by(func.coalesce(func.sum(total_cost_expr), 0).desc())
        .all()
    )

    return MaterialCostByServiceResponse(
        salon_id=salon_id,
        date_from=effective_date_from,
        date_to=effective_date_to,
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


@router.get("/payments", response_model=PaymentsReportResponse)
async def payments_report(
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
            PaymentAllocation.method.label("method"),
            Payment.client_id.label("client_id"),
            Customer.display_name.label("client_name"),
            func.count(func.distinct(Payment.id)).label("payments_count"),
            func.coalesce(func.sum(PaymentAllocation.amount), 0).label("total_amount"),
            func.coalesce(func.sum(case((Payment.client_card_id.isnot(None), 1), else_=0)), 0).label("card_payments_count"),
        )
        .join(PaymentAllocation, PaymentAllocation.payment_id == Payment.id)
        .outerjoin(Customer, Customer.id == Payment.client_id)
    )
    query = _apply_salon_scope(query, Payment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, Payment.paid_at, date_from, date_to)
    rows = (
        query.group_by(PaymentAllocation.method, Payment.client_id, Customer.display_name)
        .order_by(func.coalesce(func.sum(PaymentAllocation.amount), 0).desc())
        .all()
    )
    return PaymentsReportResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            PaymentsReportRow(
                method=row.method,
                client_id=row.client_id,
                client_name=row.client_name,
                payments_count=int(row.payments_count or 0),
                total_amount=float(row.total_amount or 0),
                card_payments_count=int(row.card_payments_count or 0),
            )
            for row in rows
        ],
    )


@router.get("/service-demand", response_model=ServiceDemandResponse)
async def service_demand_report(
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
            AppointmentPerformedLine.service_id.label("service_id"),
            func.coalesce(AppointmentPerformedLine.service_name_snapshot, ServiceCatalogItem.name).label("service_name"),
            func.count(AppointmentPerformedLine.id).label("performed_count"),
            func.coalesce(func.avg(AppointmentPerformedLine.price_snapshot), 0).label("avg_sold_price"),
            func.coalesce(func.avg(func.coalesce(AppointmentPerformedLine.list_price_snapshot, AppointmentPerformedLine.price_snapshot)), 0).label("avg_list_price"),
            func.coalesce(func.avg(func.coalesce(AppointmentPerformedLine.discount_allocated_snapshot, 0)), 0).label("avg_discount"),
            func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0).label("total_revenue"),
        )
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)

    rows = (
        query.group_by(AppointmentPerformedLine.service_id, func.coalesce(AppointmentPerformedLine.service_name_snapshot, ServiceCatalogItem.name))
        .order_by(func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0).desc())
        .all()
    )
    return ServiceDemandResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            ServiceDemandRow(
                service_id=row.service_id,
                service_name=row.service_name,
                performed_count=int(row.performed_count or 0),
                avg_sold_price=float(row.avg_sold_price or 0),
                avg_list_price=float(row.avg_list_price or 0),
                avg_discount=float(row.avg_discount or 0),
                total_revenue=float(row.total_revenue or 0),
            )
            for row in rows
        ],
    )


@router.get("/service-margin", response_model=ServiceMarginResponse)
async def service_margin_report(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    line_costs = (
        db.query(
            PerformedLineResource.performedline_id.label("performed_line_id"),
            _performed_line_costs_subquery().label("material_cost"),
        )
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
        .group_by(PerformedLineResource.performedline_id)
        .subquery()
    )

    query = (
        db.query(
            AppointmentPerformedLine.service_id.label("service_id"),
            func.coalesce(AppointmentPerformedLine.service_name_snapshot, ServiceCatalogItem.name).label("service_name"),
            func.count(AppointmentPerformedLine.id).label("performed_count"),
            func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0).label("total_revenue"),
            func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0).label("total_material_cost"),
        )
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .outerjoin(line_costs, line_costs.c.performed_line_id == AppointmentPerformedLine.id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)

    rows = (
        query.group_by(AppointmentPerformedLine.service_id, func.coalesce(AppointmentPerformedLine.service_name_snapshot, ServiceCatalogItem.name))
        .order_by((func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0) - func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0)).desc())
        .all()
    )

    return ServiceMarginResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            ServiceMarginRow(
                service_id=row.service_id,
                service_name=row.service_name,
                performed_count=int(row.performed_count or 0),
                total_revenue=float(row.total_revenue or 0),
                total_material_cost=float(row.total_material_cost or 0),
                total_margin=float((row.total_revenue or 0) - (row.total_material_cost or 0)),
                avg_margin_per_service=float(
                    (((row.total_revenue or 0) - (row.total_material_cost or 0)) / row.performed_count)
                    if (row.performed_count or 0)
                    else 0
                ),
            )
            for row in rows
        ],
    )


@router.get("/staff-performance", response_model=StaffPerformanceResponse)
async def staff_performance_report(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    line_costs = (
        db.query(
            PerformedLineResource.performedline_id.label("performed_line_id"),
            _performed_line_costs_subquery().label("material_cost"),
        )
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
        .group_by(PerformedLineResource.performedline_id)
        .subquery()
    )

    query = (
        db.query(
            AppointmentPerformedLine.worker_id.label("staff_id"),
            StaffMember.display_name.label("staff_name"),
            func.count(AppointmentPerformedLine.id).label("performed_count"),
            func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0).label("total_revenue"),
            func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0).label("total_material_cost"),
        )
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(StaffMember, StaffMember.id == AppointmentPerformedLine.worker_id)
        .outerjoin(line_costs, line_costs.c.performed_line_id == AppointmentPerformedLine.id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)

    rows = (
        query.group_by(AppointmentPerformedLine.worker_id, StaffMember.display_name)
        .order_by((func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0) - func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0)).desc())
        .all()
    )

    return StaffPerformanceResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            StaffPerformanceRow(
                staff_id=row.staff_id,
                staff_name=row.staff_name,
                performed_count=int(row.performed_count or 0),
                total_revenue=float(row.total_revenue or 0),
                total_material_cost=float(row.total_material_cost or 0),
                total_margin=float((row.total_revenue or 0) - (row.total_material_cost or 0)),
                avg_revenue_per_service=float(((row.total_revenue or 0) / row.performed_count) if (row.performed_count or 0) else 0),
                avg_margin_per_service=float(
                    (((row.total_revenue or 0) - (row.total_material_cost or 0)) / row.performed_count)
                    if (row.performed_count or 0)
                    else 0
                ),
            )
            for row in rows
        ],
    )


@router.get("/material-usage/by-family", response_model=MaterialUsageByFamilyResponse)
async def material_usage_by_family(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    effective_family = func.coalesce(
        PerformedLineResource.product_family_snapshot,
        LegacyProductCatalogItem.family_code,
    )
    total_cost_expr = func.coalesce(
        PerformedLineResource.total_cost_snapshot,
        PerformedLineResource.quantity_used
        * func.coalesce(
            PerformedLineResource.unit_cost_snapshot,
            LegacyProductCatalogItem.purchase_price,
            LegacyProductCatalogItem.purchase_price_c,
            LegacyProductCatalogItem.catalog_net_price,
            0,
        ),
        0,
    )
    query = (
        db.query(
            effective_family.label("product_family"),
            func.count(PerformedLineResource.id).label("lines_count"),
            func.coalesce(func.sum(PerformedLineResource.quantity_used), 0).label("total_quantity"),
            func.coalesce(func.sum(total_cost_expr), 0).label("total_cost"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(AppointmentPerformedLine.worker_id == current_staff.id)

    rows = (
        query.group_by(effective_family)
        .order_by(func.coalesce(func.sum(total_cost_expr), 0).desc())
        .all()
    )

    return MaterialUsageByFamilyResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            MaterialUsageByFamilyRow(
                product_family=row.product_family,
                lines_count=int(row.lines_count or 0),
                total_quantity=float(row.total_quantity or 0),
                total_cost=float(row.total_cost or 0),
            )
            for row in rows
        ],
    )


@router.get("/bundle-margin", response_model=BundleMarginResponse)
async def bundle_margin_report(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    line_costs = (
        db.query(
            PerformedLineResource.performedline_id.label("performed_line_id"),
            _performed_line_costs_subquery().label("material_cost"),
        )
        .outerjoin(LegacyProductCatalogItem, LegacyProductCatalogItem.id == PerformedLineResource.product_id)
        .group_by(PerformedLineResource.performedline_id)
        .subquery()
    )

    query = (
        db.query(
            AppointmentPerformedLine.bundle_id_snapshot.label("bundle_id"),
            BundleCatalog.name.label("bundle_name"),
            func.count(AppointmentPerformedLine.id).label("performed_lines"),
            func.count(func.distinct(AppointmentPerformedLine.appointment_id)).label("appointments_count"),
            func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0).label("total_revenue"),
            func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0).label("total_material_cost"),
        )
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(BundleCatalog, BundleCatalog.id == AppointmentPerformedLine.bundle_id_snapshot)
        .outerjoin(line_costs, line_costs.c.performed_line_id == AppointmentPerformedLine.id)
        .filter(AppointmentPerformedLine.sold_as_bundle.is_(True), AppointmentPerformedLine.bundle_id_snapshot.isnot(None))
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)

    rows = (
        query.group_by(AppointmentPerformedLine.bundle_id_snapshot, BundleCatalog.name)
        .order_by((func.coalesce(func.sum(AppointmentPerformedLine.price_snapshot), 0) - func.coalesce(func.sum(func.coalesce(line_costs.c.material_cost, 0)), 0)).desc())
        .all()
    )

    return BundleMarginResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            BundleMarginRow(
                bundle_id=row.bundle_id,
                bundle_name=row.bundle_name,
                performed_lines=int(row.performed_lines or 0),
                appointments_count=int(row.appointments_count or 0),
                total_revenue=float(row.total_revenue or 0),
                total_material_cost=float(row.total_material_cost or 0),
                total_margin=float((row.total_revenue or 0) - (row.total_material_cost or 0)),
                avg_margin_per_appointment=float(
                    (((row.total_revenue or 0) - (row.total_material_cost or 0)) / row.appointments_count)
                    if (row.appointments_count or 0)
                    else 0
                ),
            )
            for row in rows
        ],
    )


@router.get("/recipe-deviation/by-staff", response_model=MaterialDeviationByStaffResponse)
async def recipe_deviation_by_staff(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    planned_expr = _recipe_planned_quantity_expr()
    query = (
        db.query(
            AppointmentPerformedLine.worker_id.label("staff_id"),
            StaffMember.display_name.label("staff_name"),
            func.count(PerformedLineResource.id).label("lines_count"),
            func.coalesce(func.sum(planned_expr), 0).label("total_planned"),
            func.coalesce(func.sum(PerformedLineResource.quantity_used), 0).label("total_actual"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(StaffMember, StaffMember.id == AppointmentPerformedLine.worker_id)
        .outerjoin(ServiceRecipeItem, ServiceRecipeItem.id == PerformedLineResource.recipeitem_id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)
    if current_user.role == UserRole.EMPLOYEE:
        if current_staff is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")
        query = query.filter(AppointmentPerformedLine.worker_id == current_staff.id)

    rows = (
        query.group_by(AppointmentPerformedLine.worker_id, StaffMember.display_name)
        .order_by((func.coalesce(func.sum(PerformedLineResource.quantity_used), 0) - func.coalesce(func.sum(planned_expr), 0)).desc())
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


@router.get("/recipe-deviation/by-service", response_model=RecipeDeviationByServiceResponse)
async def recipe_deviation_by_service(
    salon_id: int | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    planned_expr = _recipe_planned_quantity_expr()
    service_name_expr = func.coalesce(AppointmentPerformedLine.service_name_snapshot, ServiceCatalogItem.name)
    query = (
        db.query(
            AppointmentPerformedLine.service_id.label("service_id"),
            service_name_expr.label("service_name"),
            func.count(PerformedLineResource.id).label("lines_count"),
            func.coalesce(func.sum(planned_expr), 0).label("total_planned"),
            func.coalesce(func.sum(PerformedLineResource.quantity_used), 0).label("total_actual"),
        )
        .join(AppointmentPerformedLine, AppointmentPerformedLine.id == PerformedLineResource.performedline_id)
        .join(Appointment, Appointment.id == AppointmentPerformedLine.appointment_id)
        .outerjoin(ServiceCatalogItem, ServiceCatalogItem.id == AppointmentPerformedLine.service_id)
        .outerjoin(ServiceRecipeItem, ServiceRecipeItem.id == PerformedLineResource.recipeitem_id)
    )
    query = _apply_salon_scope(query, Appointment.salon_id, salon_id, db, current_user, current_staff)
    query = _apply_date_range(query, AppointmentPerformedLine.performed_at, date_from, date_to)
    rows = (
        query.group_by(AppointmentPerformedLine.service_id, service_name_expr)
        .order_by((func.coalesce(func.sum(PerformedLineResource.quantity_used), 0) - func.coalesce(func.sum(planned_expr), 0)).desc())
        .all()
    )
    return RecipeDeviationByServiceResponse(
        salon_id=salon_id,
        date_from=date_from,
        date_to=date_to,
        rows=[
            RecipeDeviationByServiceRow(
                service_id=row.service_id,
                service_name=row.service_name,
                lines_count=int(row.lines_count or 0),
                total_planned=float(row.total_planned or 0),
                total_actual=float(row.total_actual or 0),
                deviation=float((row.total_actual or 0) - (row.total_planned or 0)),
            )
            for row in rows
        ],
    )
