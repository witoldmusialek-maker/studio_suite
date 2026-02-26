"""
Schemas for legacy-imported salon reports.
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class LegacyImportSummaryResponse(BaseModel):
    salons: int
    services: int
    bundles: int
    forfait_transactions: int
    fiche_lines: int
    edition1_days: int


class BundleRevenueRow(BaseModel):
    bundle_code: str
    bundle_name: str
    count: int
    revenue: float


class LegacyForfaitsReportResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[BundleRevenueRow]


class ServiceWorkerRevenueRow(BaseModel):
    worker_code: str
    worker_name: str
    service_code: str
    service_name: str
    qty: int
    revenue: float


class LegacyServiceReportResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[ServiceWorkerRevenueRow]


class LegacyMonthlySummaryRow(BaseModel):
    month: str
    days_count: int
    gross_total: float
    net_total: float
    vat_total: float
    tickets_count: int


class LegacyMonthlySummaryResponse(BaseModel):
    rows: List[LegacyMonthlySummaryRow]


class LegacyDailySummaryRow(BaseModel):
    date: str
    day_name: str
    gross_total: float
    net_total: float
    vat_total: float
    tickets_count: int


class LegacyDailySummaryResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[LegacyDailySummaryRow]


class LegacyForfaitTransactionRow(BaseModel):
    date_token: str
    bundle_code: str
    bundle_name: str
    price: float


class LegacyForfaitTransactionResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[LegacyForfaitTransactionRow]


class LegacyServiceAggregateRow(BaseModel):
    service_code: str
    service_name: str
    qty: int
    revenue: float


class LegacyServiceAggregateResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[LegacyServiceAggregateRow]


class LegacyCashflowRow(BaseModel):
    date: str
    payment_hint: str
    count: int
    revenue: float


class LegacyCashflowResponse(BaseModel):
    from_date: Optional[date]
    to_date: Optional[date]
    rows: List[LegacyCashflowRow]


class LegacyStat7WorkerRow(BaseModel):
    worker_code: str
    worker_name: str
    total: float
    payment_a: str
    payment_b: str
    payment_c: str


class LegacyStat7WorkerResponse(BaseModel):
    rows: List[LegacyStat7WorkerRow]
