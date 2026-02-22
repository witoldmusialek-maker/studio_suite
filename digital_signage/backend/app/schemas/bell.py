"""
Schematy dzwonkow szkolnych
"""
from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel


class BellScheduleBase(BaseModel):
    """Podstawowy schemat harmonogramu dzwonka"""
    name: str
    bell_time: time
    event_type: str = 'lesson'  # 'lesson' = na lekcję, 'break' = na przerwę
    sound_file_path: Optional[str] = None
    volume: int = 50
    group_id: Optional[int] = None
    playlist_id: Optional[int] = None


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
    event_type: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sound_file_path: Optional[str] = None
    volume: Optional[int] = None
    play_on_displays: Optional[bool] = None
    display_ids: Optional[List[int]] = None
    group_id: Optional[int] = None
    playlist_id: Optional[int] = None
    active: Optional[bool] = None


class BellScheduleResponse(BellScheduleBase):
    """Schemat odpowiedzi harmonogramu dzwonka"""
    id: int
    event_type: str = 'lesson'
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    play_on_displays: bool
    display_ids: Optional[List[int]] = None
    group_id: Optional[int] = None
    playlist_id: Optional[int] = None
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
    """Komenda odtwarzania dzwonka dla wyswietlacza"""
    bell_schedule_id: int
    sound_file_path: str
    volume: int


class BellMarkPlayedRequest(BaseModel):
    """Zgloszenie odtworzenia dzwonka przez klienta."""
    bell_schedule_id: Optional[int] = None
    bell_id: Optional[int] = None
    display_id: Optional[int] = None
    status: str = "played"
    error_message: Optional[str] = None


class BellRuntimePauseRequest(BaseModel):
    """Pause bells globally for N minutes."""
    minutes: int = 15
    reason: Optional[str] = None


class BellRuntimeControlResponse(BaseModel):
    """Runtime status for bells engine."""
    bells_enabled: bool
    pause_until: Optional[datetime] = None
    pause_reason: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BellCalendarOverrideCreate(BaseModel):
    """Create/replace date override for bells."""
    day: Optional[date] = None  # None = szablon (do wykorzystania w kalendarzu)
    bells_enabled: bool = True
    reason: Optional[str] = None


class BellCalendarOverrideResponse(BaseModel):
    """Date override for bells."""
    id: int
    day: Optional[date] = None  # None = szablon
    bells_enabled: bool
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BellProfileCreate(BaseModel):
    name: str
    month: Optional[int] = None
    is_default: bool = False
    is_active: bool = True


class BellProfileUpdate(BaseModel):
    name: Optional[str] = None
    month: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class BellProfileResponse(BaseModel):
    id: int
    name: str
    month: Optional[int] = None
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BellProfileOverrideCreate(BaseModel):
    day: date
    profile_id: int
    reason: Optional[str] = None


class BellProfileOverrideResponse(BaseModel):
    id: int
    day: date
    profile_id: int
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BellScheduleProfilesUpdate(BaseModel):
    profile_ids: List[int]


class BellSoundResponse(BaseModel):
    id: int
    name: str
    file_path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BellSoundRenameRequest(BaseModel):
    name: str


class BellProfilePlaceholderUpsert(BaseModel):
    placeholder_key: str
    sound_id: int


class BellProfilePlaceholderResponse(BaseModel):
    id: int
    profile_id: int
    placeholder_key: str
    sound_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BellMusicScheduleBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    display_ids: Optional[List[int]] = None
    profile_ids: Optional[List[int]] = None
    volume: int = 50
    priority: int = 0
    active: bool = True


class BellMusicScheduleCreate(BellMusicScheduleBase):
    pass


class BellMusicScheduleUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    display_ids: Optional[List[int]] = None
    profile_ids: Optional[List[int]] = None
    volume: Optional[int] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class BellMusicScheduleResponse(BellMusicScheduleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BellMusicTrackCreate(BaseModel):
    file_path: Optional[str] = None
    sound_id: Optional[int] = None
    placeholder_key: Optional[str] = None
    title: Optional[str] = None
    sort_order: int = 0
    active: bool = True


class BellMusicTrackResponse(BaseModel):
    id: int
    schedule_id: int
    file_path: str
    title: Optional[str] = None
    sort_order: int
    active: bool
    sound_id: Optional[int] = None
    placeholder_key: Optional[str] = None
    resolved_sound_id: Optional[int] = None
    resolved_file_path: Optional[str] = None
    resolved_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
