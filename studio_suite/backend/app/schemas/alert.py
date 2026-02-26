"""
Schematy alertów
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertBase(BaseModel):
    """Podstawowy schemat alertu"""
    alert_type: str
    severity: str
    message: str


class AlertCreate(AlertBase):
    """Schemat tworzenia alertu"""
    display_id: int


class AlertResponse(AlertBase):
    """Schemat odpowiedzi alertu"""
    id: int
    display_id: int
    resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Schemat aktualizacji alertu"""
    resolved: Optional[bool] = None


class DisplayStatusHistoryResponse(BaseModel):
    """Schemat historii statusów"""
    id: int
    display_id: int
    status: str
    last_seen: Optional[datetime] = None
    connection_lost_at: Optional[datetime] = None
    connection_restored_at: Optional[datetime] = None
    duration_offline_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True



