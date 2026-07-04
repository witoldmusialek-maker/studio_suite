"""Schemas for transitional Legacy CAISSE cashier flow."""
from datetime import date, datetime

from pydantic import BaseModel, Field


class LegacyCaisseStaffRow(BaseModel):
    staff_id: int
    staff_code: str
    staff_name: str
    role_name: str | None = None
    is_active: bool = True


class LegacyCaisseServiceRow(BaseModel):
    service_id: int
    service_code: str
    service_name: str
    service_segment: str
    price: float
    duration_minutes: int = 0
    is_product_shortcut: bool = False


class LegacyCaisseBundleItemRow(BaseModel):
    position: int
    service_id: int | None = None
    service_code: str
    service_name: str
    price: float


class LegacyCaisseBundleRow(BaseModel):
    bundle_id: int
    bundle_code: str
    bundle_name: str
    price: float
    items: list[LegacyCaisseBundleItemRow]


class LegacyCaisseProductRow(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    price: float
    fiscal_code: str | None = None


class LegacyCaisseCashSessionRead(BaseModel):
    id: int | None = None
    salon_id: int
    business_date: date
    opening_cash: float = 0
    closing_cash: float | None = None
    status: str = "OPEN"


class LegacyCaisseContextResponse(BaseModel):
    salon_id: int
    business_date: date
    staff: list[LegacyCaisseStaffRow]
    services: list[LegacyCaisseServiceRow]
    bundles: list[LegacyCaisseBundleRow]
    products: list[LegacyCaisseProductRow]
    payment_methods: list[str]
    cash_session: LegacyCaisseCashSessionRead | None = None


class LegacyCaisseLineWrite(BaseModel):
    line_kind: str = Field(default="service", max_length=24)
    staff_id: int
    service_id: int | None = None
    product_id: int | None = None
    bundle_id: int | None = None
    legacy_worker_code: str = Field(max_length=16)
    legacy_service_code: str = Field(max_length=32)
    label: str = Field(min_length=1, max_length=255)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(ge=0)
    discount_amount: float = Field(default=0, ge=0)


class LegacyCaissePaymentAllocationWrite(BaseModel):
    method: str = Field(min_length=1, max_length=32)
    amount: float = Field(gt=0)
    voucher_reference: str | None = Field(default=None, max_length=128)


class LegacyCaisseFicheCreate(BaseModel):
    salon_id: int
    customer_id: int | None = None
    appointment_id: int | None = None
    sale_time: datetime | None = None
    motivation: str | None = Field(default=None, max_length=64)
    payment_method: str = Field(default="cash", max_length=32)
    status: str = Field(default="COMPLETED", max_length=16)
    lines: list[LegacyCaisseLineWrite] = Field(min_length=1)
    allocations: list[LegacyCaissePaymentAllocationWrite] = Field(default_factory=list)


class LegacyCaisseLineRead(BaseModel):
    id: int
    line_kind: str
    staff_id: int | None = None
    service_id: int | None = None
    product_id: int | None = None
    bundle_id: int | None = None
    legacy_worker_code: str | None = None
    legacy_service_code: str | None = None
    label: str
    quantity: float
    unit_price: float
    discount_amount: float
    total_gross: float


class LegacyCaisseFicheRead(BaseModel):
    sale_id: int
    payment_id: int | None = None
    salon_id: int
    customer_id: int | None = None
    appointment_id: int | None = None
    sale_time: datetime
    status: str
    total_gross: float
    service_gross: float = 0
    retail_gross: float = 0
    discount_total: float = 0
    payment_method: str | None = None
    lines: list[LegacyCaisseLineRead]


class LegacyCaisseVoidResponse(BaseModel):
    sale_id: int
    status: str


class LegacyCaisseCashSessionWrite(BaseModel):
    salon_id: int
    business_date: date | None = None
    opening_cash: float = Field(default=0, ge=0)
    closing_cash: float | None = Field(default=None, ge=0)
    status: str = Field(default="OPEN", max_length=16)


class LegacyCaisseExpenseWrite(BaseModel):
    salon_id: int
    expense_date: date | None = None
    staff_id: int | None = None
    expense_type: str = Field(default="misc", max_length=32)
    family: str | None = Field(default=None, max_length=128)
    label: str = Field(min_length=1, max_length=255)
    amount_gross: float = Field(ge=0)
    vat_amount: float = Field(default=0, ge=0)


class LegacyCaisseExpenseRead(BaseModel):
    id: int
    salon_id: int
    expense_date: date
    staff_id: int | None = None
    expense_type: str
    family: str | None = None
    label: str
    amount_gross: float
    vat_amount: float
    amount_net: float


class LegacyCaissePresenceWrite(BaseModel):
    salon_id: int
    staff_id: int
    presence_date: date | None = None
    status: str = Field(default="PRESENT", max_length=24)
    time_from: str | None = Field(default=None, max_length=8)
    time_to: str | None = Field(default=None, max_length=8)


class LegacyCaissePresenceRead(BaseModel):
    id: int
    salon_id: int
    staff_id: int
    presence_date: date
    status: str
    time_from: str | None = None
    time_to: str | None = None
