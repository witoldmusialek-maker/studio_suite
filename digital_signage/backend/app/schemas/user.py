"""
Schematy użytkownika
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Podstawowy schemat użytkownika"""
    username: str
    role: UserRole


class UserCreate(UserBase):
    """Schemat tworzenia użytkownika"""
    password: str


class UserLogin(BaseModel):
    """Schemat logowania"""
    username: str
    password: str


class UserResponse(UserBase):
    """Schemat odpowiedzi użytkownika"""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schemat aktualizacji użytkownika przez admina"""
    role: UserRole


class PasswordChangeRequest(BaseModel):
    """Zmiana hasła zalogowanego użytkownika"""
    current_password: str
    new_password: str = Field(min_length=6)


class PasswordResetRequest(BaseModel):
    """Reset hasła użytkownika przez admina"""
    new_password: Optional[str] = Field(default=None, min_length=6)


class PasswordResetResponse(BaseModel):
    """Odpowiedź po resecie hasła"""
    user_id: int
    temporary_password: Optional[str] = None
    message: str

