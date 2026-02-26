"""
Schematy wyświetlacza
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DisplayBase(BaseModel):
    """Podstawowy schemat wyświetlacza"""
    name: str
    orientation: int = 0
    resolution_width: int = 1920
    resolution_height: int = 1080
    floor: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    cache_size_mb: int = 1000


class DisplayCreate(DisplayBase):
    """Schemat tworzenia wyświetlacza"""
    mac_address: str


class DisplayUpdate(BaseModel):
    """Schemat aktualizacji wyświetlacza"""
    name: Optional[str] = None
    orientation: Optional[int] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    group_id: Optional[int] = None
    floor: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    cache_size_mb: Optional[int] = None


class DisplayRegister(BaseModel):
    """Schemat rejestracji wyświetlacza (przez MAC address)"""
    mac_address: str
    ip_address: Optional[str] = None
    resolution_width: int = 1920
    resolution_height: int = 1080


class DisplayHeartbeat(BaseModel):
    """Schemat heartbeat od wyświetlacza"""
    current_content_id: Optional[int] = None
    current_content_type: Optional[str] = None
    is_playing_video: Optional[bool] = None
    cache_status: Optional[dict] = None
    errors: Optional[list] = None


class DisplayResponse(DisplayBase):
    """Schemat odpowiedzi wyświetlacza"""
    id: int
    mac_address: str
    ip_address: Optional[str] = None
    status: str
    group_id: Optional[int] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DisplayStatusResponse(BaseModel):
    """Schemat statusu wyświetlacza"""
    id: int
    name: str
    status: str
    last_seen: Optional[datetime] = None
    current_content_id: Optional[int] = None
    floor: Optional[str] = None
    group_id: Optional[int] = None

