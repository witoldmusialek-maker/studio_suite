"""
Schematy dzwonków szkolnych
"""
from pydantic import BaseModel
from datetime import datetime, time, date
from typing import Optional, List


class BellScheduleBase(BaseModel):
    """Podstawowy schemat harmonogramu dzwonka"""
    name: str
    bell_time: time
    sound_file_path: Optional[str] = None
    volume: int = 50


class BellScheduleCreate(BellScheduleBase):
    """Schemat tworzenia harmonogramu dzwonka"""
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    play_on_displays: bool = True
    display_ids: Optional[List[int]] = None


class BellScheduleUpdate(BaseModel):
    """Schemat aktualizacji harmonogramu dzwonka"""
    name: Optional[str] = None
    bell_time: Optional[time] = None
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sound_file_path: Optional[str] = None
    volume: Optional[int] = None
    play_on_displays: Optional[bool] = None
    display_ids: Optional[List[int]] = None
    active: Optional[bool] = None


class BellScheduleResponse(BellScheduleBase):
    """Schemat odpowiedzi harmonogramu dzwonka"""
    id: int
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    play_on_displays: bool
    display_ids: Optional[List[int]] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BellHistoryResponse(BaseModel):
    """Schemat historii odtworzenia dzwonka"""
    id: int
    bell_schedule_id: int
    played_at: datetime
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BellPlayCommand(BaseModel):
    """Komenda odtwarzania dzwonka dla wyświetlacza"""
    bell_schedule_id: int
    sound_file_path: str
    volume: int



