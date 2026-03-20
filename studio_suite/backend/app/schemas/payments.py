"""Payments and invoice schemas."""
from datetime import date, datetime

from pydantic import BaseModel, Field


class ClientCardWrite(BaseModel):
    discount_pct: float = Field(ge=0, le=100)
    expiry: date | None = None


class ClientCardRead(BaseModel):
    id: int
    client_id: int
    discount_pct: float
    expiry: date | None = None


class InvitationWrite(BaseModel):
    service_id: int
    expiry: date | None = None


class InvitationRead(BaseModel):
    id: int
    client_id: int
    service_id: int
    expiry: date | None = None
    used_on_payment_id: int | None = None


class AppointmentInvoiceItem(BaseModel):
    service_id: int | None = None
    product_id: int | None = None
    kind: str
    label: str
    quantity: float
    unit_price: float
    total_gross: float
    discount_value: float = 0


class AppointmentInvoiceRead(BaseModel):
    appointment_id: int
    client_id: int
    service_gross: float
    retail_gross: float
    card_discount: float
    invitation_discount: float
    total_discount: float
    net_total: float
    eligible_card: ClientCardRead | None = None
    available_invitations: list[InvitationRead]
    items: list[AppointmentInvoiceItem]


class PaymentRetailItemWrite(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)


class PaymentAllocationWrite(BaseModel):
    method: str
    amount: float = Field(gt=0)
    voucher_reference: str | None = Field(default=None, max_length=128)


class PaymentWrite(BaseModel):
    amount: float = Field(ge=0)
    method: str
    use_card: bool = False
    invitation_ids: list[int] = Field(default_factory=list)
    retail_items: list[PaymentRetailItemWrite] = Field(default_factory=list)
    allocations: list[PaymentAllocationWrite] = Field(default_factory=list)
    promotion_id: int | None = None
    promotion_name: str | None = Field(default=None, max_length=255)


class PaymentAllocationRead(BaseModel):
    id: int
    method: str
    amount: float
    voucher_reference: str | None = None


class PromotionRead(BaseModel):
    id: int
    name: str
    promotion_type: str
    value: float
    salon_id: int | None = None
    service_id: int | None = None
    bundle_id: int | None = None
    customer_tier: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True


class PromotionWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    promotion_type: str = Field(min_length=1, max_length=32)
    value: float = Field(ge=0)
    salon_id: int | None = None
    service_id: int | None = None
    bundle_id: int | None = None
    customer_tier: str | None = Field(default=None, max_length=32)
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True


class PaymentLineRead(BaseModel):
    id: int
    item_kind: str
    label: str
    quantity: float
    unit_price: float
    total_gross: float
    service_id: int | None = None
    product_id: int | None = None
    invitation_id: int | None = None


class PaymentRead(BaseModel):
    id: int
    appointment_id: int
    salon_id: int
    client_id: int
    created_by_user_id: int
    sale_id: int | None = None
    client_card_id: int | None = None
    promotion_id: int | None = None
    method: str
    amount: float
    service_gross: float
    retail_gross: float
    discount_total: float
    discount_reason_snapshot: str | None = None
    promotion_name_snapshot: str | None = None
    paid_at: datetime
    status: str
    allocations: list[PaymentAllocationRead]
    lines: list[PaymentLineRead]
    pdf_url: str | None = None
