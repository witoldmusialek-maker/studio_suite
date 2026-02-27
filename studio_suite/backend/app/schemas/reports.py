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
