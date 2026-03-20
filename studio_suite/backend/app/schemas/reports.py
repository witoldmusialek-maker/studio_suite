"""Operational reports schemas (read-only)."""
from datetime import date

from pydantic import BaseModel


class MaterialUsageByStaffRow(BaseModel):
    staff_id: int | None = None
    staff_name: str | None = None
    services_count: int
    lines_count: int
    total_quantity: float
    total_cost: float


class MaterialUsageByStaffResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[MaterialUsageByStaffRow]


class MaterialDeviationByStaffRow(BaseModel):
    staff_id: int | None = None
    staff_name: str | None = None
    lines_count: int
    total_planned: float
    total_actual: float
    deviation: float


class MaterialDeviationByStaffResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[MaterialDeviationByStaffRow]


class MaterialCostByServiceRow(BaseModel):
    service_id: int | None = None
    service_name: str | None = None
    lines_count: int
    total_quantity: float
    total_cost: float


class MaterialCostByServiceResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[MaterialCostByServiceRow]


class SalesBySalonRow(BaseModel):
    salon_id: int
    salon_name: str | None = None
    sales_count: int
    transactions_count: int
    lines_count: int
    total_gross: float


class SalesBySalonResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[SalesBySalonRow]


class PaymentsReportRow(BaseModel):
    method: str
    client_id: int | None = None
    client_name: str | None = None
    payments_count: int
    total_amount: float
    card_payments_count: int


class PaymentsReportResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[PaymentsReportRow]


class ServiceDemandRow(BaseModel):
    service_id: int | None = None
    service_name: str | None = None
    performed_count: int
    avg_sold_price: float
    avg_list_price: float
    avg_discount: float
    total_revenue: float


class ServiceDemandResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[ServiceDemandRow]


class ServiceMarginRow(BaseModel):
    service_id: int | None = None
    service_name: str | None = None
    performed_count: int
    total_revenue: float
    total_material_cost: float
    total_margin: float
    avg_margin_per_service: float


class ServiceMarginResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[ServiceMarginRow]


class StaffPerformanceRow(BaseModel):
    staff_id: int | None = None
    staff_name: str | None = None
    performed_count: int
    total_revenue: float
    total_material_cost: float
    total_margin: float
    avg_revenue_per_service: float
    avg_margin_per_service: float


class StaffPerformanceResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[StaffPerformanceRow]


class MaterialUsageByFamilyRow(BaseModel):
    product_family: str | None = None
    lines_count: int
    total_quantity: float
    total_cost: float


class MaterialUsageByFamilyResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[MaterialUsageByFamilyRow]


class BundleMarginRow(BaseModel):
    bundle_id: int | None = None
    bundle_name: str | None = None
    performed_lines: int
    appointments_count: int
    total_revenue: float
    total_material_cost: float
    total_margin: float
    avg_margin_per_appointment: float


class BundleMarginResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[BundleMarginRow]


class RecipeDeviationByServiceRow(BaseModel):
    service_id: int | None = None
    service_name: str | None = None
    lines_count: int
    total_planned: float
    total_actual: float
    deviation: float


class RecipeDeviationByServiceResponse(BaseModel):
    salon_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    rows: list[RecipeDeviationByServiceRow]
