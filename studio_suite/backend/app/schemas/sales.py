"""Sales schemas (MVP)."""
from datetime import datetime

from pydantic import BaseModel, Field


class SaleLineCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_price_gross: float = Field(ge=0)


class SaleCreate(BaseModel):
    salon_id: int
    customer_id: int | None = None
    appointment_id: int | None = None
    sale_time: datetime
    lines: list[SaleLineCreate] = Field(min_length=1)


class SaleLineRead(BaseModel):
    id: int
    product_id: int | None = None
    quantity: float
    unit: str
    unit_price_gross: float
    total_price_gross: float
    fiscal_code: str | None = None


class SaleRead(BaseModel):
    id: int
    salon_id: int
    customer_id: int | None = None
    appointment_id: int | None = None
    cashier_user_id: int
    sale_time: datetime
    total_gross: float
    status: str
    lines: list[SaleLineRead]
