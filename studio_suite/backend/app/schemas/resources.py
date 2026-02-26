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
    salon_id: int
    product_code: str = Field(min_length=1, max_length=16)
    product_name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=128)
    package_size_g: float | None = Field(default=100, ge=0)
    doses_short: float = Field(default=4, gt=0)
    doses_medium: float = Field(default=2, gt=0)
    doses_long: float = Field(default=1.25, gt=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=128)
    package_size_g: float | None = Field(default=None, ge=0)
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
    brand: str | None
    package_size_g: float | None
    doses_short: float
    doses_medium: float
    doses_long: float
    is_active: bool
