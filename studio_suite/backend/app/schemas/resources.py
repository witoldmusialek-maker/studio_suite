"""
Schemas for salon/staff resources CRUD.
"""
from pydantic import BaseModel, Field


class SalonBase(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=128)
    is_active: bool = True


class SalonCreate(SalonBase):
    pass


class SalonUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=16)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    is_active: bool | None = None


class SalonRead(SalonBase):
    id: int

    class Config:
        from_attributes = True


class StaffFunctionRead(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class StaffCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=256)
    legacy_code: str | None = Field(default=None, max_length=16)
    salon_id: int | None = None
    role_id: int | None = None
    is_active: bool = True


class StaffUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=256)
    legacy_code: str | None = Field(default=None, max_length=16)
    salon_id: int | None = None
    role_id: int | None = None
    is_active: bool | None = None


class StaffRead(BaseModel):
    id: int
    display_name: str
    salon_id: int | None
    salon_name: str | None
    role_id: int | None
    role_name: str | None
    is_active: bool
    legacy_code: str | None


class ProductCreate(BaseModel):
    salon_id: int | None = None
    product_code: str = Field(min_length=1, max_length=32)
    product_name: str = Field(min_length=1, max_length=255)
    product_name_pl: str | None = Field(default=None, max_length=255)
    fiscal_code: str | None = Field(default=None, max_length=32)
    brand: str | None = Field(default=None, max_length=128)
    package_size_g: float | None = Field(default=100, ge=0)
    catalog_net_price: float | None = Field(default=None, ge=0)
    unit_count: float | None = Field(default=None, ge=0)
    warehouse: str | None = Field(default=None, max_length=64)
    type_code: str | None = Field(default=None, max_length=16)
    purchase_price: float | None = Field(default=None, ge=0)
    family_code: str | None = Field(default=None, max_length=16)
    weight: float | None = Field(default=None, ge=0)
    package_weight: float | None = Field(default=None, ge=0)
    min_unit: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=255)
    ean: str | None = Field(default=None, max_length=64)
    salon_sale_price: float | None = Field(default=None, ge=0)
    purchase_price_c: float | None = Field(default=None, ge=0)
    is_locked: bool = False
    upsize_ts: str | None = Field(default=None, max_length=64)
    catalog_price: float | None = Field(default=None, ge=0)
    sale_price_gross: float | None = Field(default=None, ge=0)
    s_u: bool = False
    doses_short: float = Field(default=4, gt=0)
    doses_medium: float = Field(default=2, gt=0)
    doses_long: float = Field(default=1.25, gt=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    product_name_pl: str | None = Field(default=None, max_length=255)
    fiscal_code: str | None = Field(default=None, max_length=32)
    brand: str | None = Field(default=None, max_length=128)
    package_size_g: float | None = Field(default=None, ge=0)
    catalog_net_price: float | None = Field(default=None, ge=0)
    unit_count: float | None = Field(default=None, ge=0)
    warehouse: str | None = Field(default=None, max_length=64)
    type_code: str | None = Field(default=None, max_length=16)
    purchase_price: float | None = Field(default=None, ge=0)
    family_code: str | None = Field(default=None, max_length=16)
    weight: float | None = Field(default=None, ge=0)
    package_weight: float | None = Field(default=None, ge=0)
    min_unit: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=255)
    ean: str | None = Field(default=None, max_length=64)
    salon_sale_price: float | None = Field(default=None, ge=0)
    purchase_price_c: float | None = Field(default=None, ge=0)
    is_locked: bool | None = None
    upsize_ts: str | None = Field(default=None, max_length=64)
    catalog_price: float | None = Field(default=None, ge=0)
    sale_price_gross: float | None = Field(default=None, ge=0)
    s_u: bool | None = None
    doses_short: float | None = Field(default=None, gt=0)
    doses_medium: float | None = Field(default=None, gt=0)
    doses_long: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class ProductRead(BaseModel):
    salon_product_id: int
    salon_id: int
    product_id: int
    product_code: str
    product_name: str
    product_name_pl: str | None = None
    fiscal_code: str | None = None
    brand: str | None
    package_size_g: float | None
    catalog_net_price: float | None = None
    unit_count: float | None = None
    warehouse: str | None = None
    type_code: str | None = None
    purchase_price: float | None = None
    family_code: str | None = None
    weight: float | None = None
    package_weight: float | None = None
    min_unit: float | None = None
    note: str | None = None
    ean: str | None = None
    salon_sale_price: float | None = None
    purchase_price_c: float | None = None
    is_locked: bool = False
    upsize_ts: str | None = None
    catalog_price: float | None = None
    sale_price_gross: float | None = None
    s_u: bool = False
    doses_short: float
    doses_medium: float
    doses_long: float
    stock_mx03: float | None = None
    stock_mx04: float | None = None
    stock_mx07: float | None = None
    stock_100: float | None = None
    is_active: bool
