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

