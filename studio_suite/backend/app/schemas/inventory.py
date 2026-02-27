"""Inventory schemas (MVP)."""
from datetime import datetime

from pydantic import BaseModel, Field


class StockLocationCreate(BaseModel):
    salon_id: int
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    location_type: str = Field(default="MIXED", max_length=16)
    is_active: bool = True


class StockLocationRead(BaseModel):
    id: int
    salon_id: int
    code: str
    name: str
    location_type: str
    is_active: bool


class StockLevelRead(BaseModel):
    id: int
    stock_location_id: int
    stock_location_name: str | None = None
    salon_id: int | None = None
    product_id: int
    product_name: str | None = None
    quantity: float
    unit: str = "PCS"


class InventoryIssueLineCreate(BaseModel):
    product_id: int | None = None
    quantity_planned: float | None = None
    quantity_actual: float | None = Field(default=None, gt=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = None


class InventoryIssueCreate(BaseModel):
    salon_id: int
    stock_location_id: int
    appointment_id: int | None = None
    service_id: int | None = None
    performed_line_id: int | None = None
    staff_id: int | None = None
    issue_time: datetime
    remarks: str | None = Field(default=None, max_length=255)
    lines: list[InventoryIssueLineCreate] = Field(min_length=1)


class InventoryIssueLineUpdate(BaseModel):
    id: int
    product_id: int | None = None
    quantity_actual: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=8)
    unit_cost: float | None = Field(default=None, ge=0)


class InventoryIssueUpdate(BaseModel):
    remarks: str | None = Field(default=None, max_length=255)
    lines: list[InventoryIssueLineUpdate] = Field(min_length=1)


class InventoryIssueLineRead(BaseModel):
    id: int
    recipe_item_id: int | None = None
    recipe_product_family: str | None = None
    recipe_note: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    appointment_id: int | None = None
    service_id: int | None = None
    performed_line_id: int | None = None
    quantity_planned: float | None = None
    quantity_actual: float | None = None
    unit: str
    unit_cost: float
    total_cost: float


class InventoryIssueRead(BaseModel):
    id: int
    salon_id: int
    stock_location_id: int
    appointment_id: int | None = None
    service_id: int | None = None
    performed_line_id: int | None = None
    staff_id: int | None = None
    issue_time: datetime
    status: str
    remarks: str | None = None
    lines: list[InventoryIssueLineRead]


class ServiceRecipeItemCreate(BaseModel):
    product_family: str | None = Field(default=None, max_length=100)
    product_id: int | None = None
    planned_quantity: float = Field(gt=0)
    unit: str = Field(default="PCS", max_length=20)
    note: str | None = Field(default=None, max_length=255)


class ServiceRecipeItemUpdate(BaseModel):
    product_family: str | None = Field(default=None, max_length=100)
    product_id: int | None = None
    planned_quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=255)


class ServiceRecipeItemRead(BaseModel):
    id: int
    service_id: int
    product_family: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    planned_quantity: float
    unit: str
    note: str | None = None
