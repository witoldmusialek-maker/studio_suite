"""
Schematy harmonogramów
"""
from pydantic import BaseModel
from datetime import datetime, time, date
from typing import Optional, List


class ScheduleBase(BaseModel):
    """Podstawowy schemat harmonogramu"""
    name: str
    content_id: int
    start_time: time
    end_time: time
    display_duration_seconds: Optional[int] = None


class ScheduleCreate(ScheduleBase):
    """Schemat tworzenia harmonogramu"""
    display_id: Optional[int] = None
    group_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[List[int]] = None  # [1,2,3,4,5] = pon-pt
    priority: int = 0


class ScheduleUpdate(BaseModel):
    """Schemat aktualizacji harmonogramu"""
    name: Optional[str] = None
    content_id: Optional[int] = None
    display_id: Optional[int] = None
    group_id: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[List[int]] = None
    priority: Optional[int] = None
    display_duration_seconds: Optional[int] = None
    active: Optional[bool] = None


class ScheduleResponse(ScheduleBase):
    """Schemat odpowiedzi harmonogramu"""
    id: int
    display_id: Optional[int] = None
    group_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[List[int]] = None
    priority: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleForDisplay(BaseModel):
    """Schemat harmonogramu dla wyświetlacza"""
    id: int
    content_id: int
    start_time: time
    end_time: time
    display_duration_seconds: Optional[int] = None
    priority: int

