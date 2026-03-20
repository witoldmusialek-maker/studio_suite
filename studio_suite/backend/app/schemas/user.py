"""
User schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    totp_code: Optional[str] = Field(default=None, min_length=6, max_length=16)


class UserResponse(UserBase):
    id: int
    tenant_id: int | None = None
    created_at: datetime
    last_login: Optional[datetime] = None
    linked_staff_id: Optional[int] = None
    linked_staff_name: Optional[str] = None
    linked_salon_id: Optional[int] = None
    linked_salon_name: Optional[str] = None
    is_superadmin: bool = False
    totp_enabled: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: UserRole


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    user_id: int
    temporary_password: Optional[str] = None
    message: str


class SessionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    role: str
    salon_id: Optional[int] = None
    salon_name: Optional[str] = None
    online_since: datetime
    last_seen: datetime
    online_seconds: int
    ip_address: Optional[str] = None
    is_active: bool = False


class TotpStatusResponse(BaseModel):
    enabled: bool


class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    qr_url: str


class TotpVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=16)


class TenantBase(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=128)
    is_active: bool = True
    billing_plan: str = Field(default="BASIC", min_length=2, max_length=32)
    billing_cycle: str = Field(default="monthly", min_length=3, max_length=16)
    monthly_base_price: float = 0
    billing_email: Optional[str] = Field(default=None, max_length=255)


class TenantCreate(TenantBase):
    admin_username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    admin_password: Optional[str] = Field(default=None, min_length=10, max_length=128)


class TenantUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=32)
    name: Optional[str] = Field(default=None, min_length=2, max_length=128)
    is_active: Optional[bool] = None
    billing_plan: Optional[str] = Field(default=None, min_length=2, max_length=32)
    billing_cycle: Optional[str] = Field(default=None, min_length=3, max_length=16)
    monthly_base_price: Optional[float] = None
    billing_email: Optional[str] = Field(default=None, max_length=255)


class TenantResponse(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool
    billing_plan: str
    billing_cycle: str
    monthly_base_price: float
    billing_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TenantModuleLicensePayload(BaseModel):
    module_code: str = Field(min_length=2, max_length=64)
    is_enabled: bool = True
    monthly_price: float = 0
    notes: Optional[str] = Field(default=None, max_length=255)


class TenantModuleLicenseResponse(TenantModuleLicensePayload):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
