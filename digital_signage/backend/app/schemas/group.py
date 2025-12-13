"""
Schematy grup wyświetlaczy
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List


class GroupBase(BaseModel):
    """Podstawowy schemat grupy"""
    name: str
    type: str
    floor: Optional[str] = None


class GroupCreate(GroupBase):
    """Schemat tworzenia grupy"""
    layout_config: Optional[Dict[str, Any]] = None


class GroupUpdate(BaseModel):
    """Schemat aktualizacji grupy"""
    name: Optional[str] = None
    type: Optional[str] = None
    floor: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None


class GroupResponse(GroupBase):
    """Schemat odpowiedzi grupy"""
    id: int
    layout_config: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GroupWithDisplays(GroupResponse):
    """Schemat grupy z listą wyświetlaczy"""
    displays: List[dict] = []

