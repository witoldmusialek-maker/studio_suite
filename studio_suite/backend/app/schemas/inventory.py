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
    product_code: str | None = None
    product_name: str | None = None
    brand: str | None = None
    family_code: str | None = None
    is_active: bool = True
    target_stock_100: float | None = None
    quantity: float
    unit: str = "PCS"
    quantity_base: float | None = None
    unit_base: str | None = None
    unit_count: float | None = None
    dose_weight: float | None = None
    package_net_weight: float | None = None


class ReplenishmentSuggestionRead(BaseModel):
    id: int
    salon_id: int
    product_id: int
    product_name: str | None = None
    target_quantity: float
    actual_quantity: float
    suggested_quantity: float
    status: str
    generated_at: datetime | None = None
    resolved_at: datetime | None = None
    note: str | None = None


class StockAdjustmentDeltaLine(BaseModel):
    product_id: int
    delta_quantity: float
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = Field(default=None, ge=0)


class StockAdjustmentDeltaCreate(BaseModel):
    salon_id: int
    stock_location_id: int | None = None
    staff_id: int | None = None
    issue_time: datetime | None = None
    remarks: str | None = Field(default=None, max_length=255)
    lines: list[StockAdjustmentDeltaLine] = Field(min_length=1)


class StockAdjustmentStocktakeLine(BaseModel):
    product_id: int
    counted_quantity: float | None = Field(default=None, ge=0)
    counted_units: float | None = Field(default=None, ge=0)
    measured_gross_weight: float | None = Field(default=None, ge=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = Field(default=None, ge=0)


class StockAdjustmentStocktakeCreate(BaseModel):
    salon_id: int
    stock_location_id: int | None = None
    staff_id: int | None = None
    issue_time: datetime | None = None
    remarks: str | None = Field(default=None, max_length=255)
    lines: list[StockAdjustmentStocktakeLine] = Field(min_length=1)


class StocktakeCandidateRead(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    unit: str
    measurement_mode: str
    dose_weight: float | None = None
    package_weight: float | None = None
    full_weight: float | None = None


class InventoryIssueLineCreate(BaseModel):
    product_id: int | None = None
    quantity_planned: float | None = None
    quantity_actual: float | None = Field(default=None, gt=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = None


class InventoryIssueCreate(BaseModel):
    salon_id: int
    stock_location_id: int | None = None
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
    variant_code: str | None = Field(default=None, max_length=32)
    position: int | None = Field(default=None, ge=1)
    product_family: str | None = Field(default=None, max_length=100)
    product_id: int | None = None
    product_label_snapshot: str | None = Field(default=None, max_length=255)
    is_optional: bool = False
    is_required: bool = True
    quantity_mode: str = Field(default="EXACT", max_length=16)
    planned_quantity: float | None = Field(default=None, gt=0)
    planned_min: float | None = Field(default=None, gt=0)
    planned_default: float | None = Field(default=None, gt=0)
    planned_max: float | None = Field(default=None, gt=0)
    unit: str = Field(default="PCS", max_length=20)
    recipe_unit_label: str | None = Field(default=None, max_length=20)
    package_unit_count: float | None = Field(default=None, gt=0)
    package_unit_label: str | None = Field(default=None, max_length=20)
    package_size_value: float | None = Field(default=None, gt=0)
    package_size_unit: str | None = Field(default=None, max_length=20)
    inventory_mode: str = Field(default="PER_SERVICE", max_length=24)
    note: str | None = Field(default=None, max_length=255)


class ServiceRecipeItemUpdate(BaseModel):
    variant_code: str | None = Field(default=None, max_length=32)
    position: int | None = Field(default=None, ge=1)
    product_family: str | None = Field(default=None, max_length=100)
    product_id: int | None = None
    product_label_snapshot: str | None = Field(default=None, max_length=255)
    is_optional: bool | None = None
    is_required: bool | None = None
    quantity_mode: str | None = Field(default=None, max_length=16)
    planned_quantity: float | None = Field(default=None, gt=0)
    planned_min: float | None = Field(default=None, gt=0)
    planned_default: float | None = Field(default=None, gt=0)
    planned_max: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    recipe_unit_label: str | None = Field(default=None, max_length=20)
    package_unit_count: float | None = Field(default=None, gt=0)
    package_unit_label: str | None = Field(default=None, max_length=20)
    package_size_value: float | None = Field(default=None, gt=0)
    package_size_unit: str | None = Field(default=None, max_length=20)
    inventory_mode: str | None = Field(default=None, max_length=24)
    note: str | None = Field(default=None, max_length=255)


class ServiceRecipeItemRead(BaseModel):
    id: int
    service_id: int
    variant_code: str | None = None
    position: int = 1
    product_family: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    product_label_snapshot: str | None = None
    is_optional: bool = False
    is_required: bool = True
    quantity_mode: str = "EXACT"
    planned_quantity: float
    planned_min: float | None = None
    planned_default: float | None = None
    planned_max: float | None = None
    unit: str
    recipe_unit_label: str | None = None
    package_unit_count: float | None = None
    package_unit_label: str | None = None
    package_size_value: float | None = None
    package_size_unit: str | None = None
    inventory_mode: str = "PER_SERVICE"
    note: str | None = None
    poj: str | None = None
    iljedn: str | None = None
    total_label: str | None = None


class PurchaseOrderLineCreate(BaseModel):
    product_id: int
    ordered_quantity: float = Field(gt=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = Field(default=None, ge=0)
    target_quantity: float | None = None
    actual_quantity: float | None = None


class PurchaseOrderCreate(BaseModel):
    salon_id: int
    note: str | None = Field(default=None, max_length=255)
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderLineRead(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    target_quantity: float | None = None
    actual_quantity: float | None = None
    ordered_quantity: float
    unit: str
    unit_cost: float | None = None
    total_cost: float | None = None


class PurchaseOrderRead(BaseModel):
    id: int
    tenant_id: int
    salon_id: int
    created_by_user_id: int | None = None
    approved_by_user_id: int | None = None
    status: str
    note: str | None = None
    created_at: datetime | None = None
    approved_at: datetime | None = None
    ordered_at: datetime | None = None
    lines: list[PurchaseOrderLineRead]


class GoodsReceiptLineCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit: str = Field(default="PCS", max_length=8)
    unit_cost: float | None = Field(default=None, ge=0)


class GoodsReceiptCreate(BaseModel):
    salon_id: int
    purchase_order_id: int | None = None
    note: str | None = Field(default=None, max_length=255)
    received_at: datetime | None = None
    lines: list[GoodsReceiptLineCreate] = Field(default_factory=list)


class GoodsReceiptLineRead(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    quantity: float
    unit: str
    unit_cost: float | None = None
    total_cost: float | None = None


class GoodsReceiptRead(BaseModel):
    id: int
    tenant_id: int
    salon_id: int
    purchase_order_id: int | None = None
    received_by_user_id: int | None = None
    status: str
    note: str | None = None
    created_at: datetime | None = None
    received_at: datetime | None = None
    posted_at: datetime | None = None
    lines: list[GoodsReceiptLineRead]


class InventoryDailyOutflowSummaryRead(BaseModel):
    day: datetime
    salon_id: int
    posted_issue_count: int
    posted_line_count: int
    total_quantity: float
    total_material_cost: float
