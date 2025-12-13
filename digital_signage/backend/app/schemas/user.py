"""
Schematy użytkownika
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

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

