"""
Schematy raportów
"""
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional, Dict, Any


class DisplayStats(BaseModel):
    """Statystyki wyświetlacza"""
    display_id: int
    display_name: str
    total_online_seconds: int
    total_offline_seconds: int
    online_percentage: float
    connection_count: int
    longest_offline_seconds: int


class DailyReportResponse(BaseModel):
    """Raport dzienny"""
    date: date
    displays: List[DisplayStats]
    total_displays: int
    average_online_percentage: float


class WeeklyReportResponse(BaseModel):
    """Raport tygodniowy"""
    week_start: date
    week_end: date
    displays: List[DisplayStats]
    total_displays: int
    average_online_percentage: float


class OfflineReportResponse(BaseModel):
    """Raport offline dla wyświetlacza"""
    display_id: int
    display_name: str
    start_date: date
    end_date: date
    total_offline_seconds: int
    total_online_seconds: int
    offline_percentage: float
    incidents: List[Dict[str, Any]]



