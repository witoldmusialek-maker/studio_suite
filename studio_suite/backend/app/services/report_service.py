"""
Serwis do generowania raportów
"""
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.display import Display
from app.models.display_status_history import DisplayStatusHistory
from app.schemas.report import DisplayStats


def get_daily_report(db: Session, report_date: date) -> Dict[str, Any]:
    """
    Generowanie raportu dziennego
    
    Args:
        db: Sesja bazy danych
        report_date: Data raportu
    
    Returns:
        Słownik z danymi raportu
    """
    start_datetime = datetime.combine(report_date, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(report_date, datetime.max.time(), tzinfo=timezone.utc)
    
    # Pobranie wszystkich wyświetlaczy
    displays = db.query(Display).all()
    
    display_stats = []
    total_online = 0
    total_offline = 0
    
    for display in displays:
        # Pobranie historii statusów dla tego dnia
        history = db.query(DisplayStatusHistory).filter(
            and_(
                DisplayStatusHistory.display_id == display.id,
                DisplayStatusHistory.created_at >= start_datetime,
                DisplayStatusHistory.created_at <= end_datetime
            )
        ).order_by(DisplayStatusHistory.created_at).all()
        
        # Obliczenie statystyk
        online_seconds = 0
        offline_seconds = 0
        connection_count = 0
        longest_offline = 0
        
        current_status = None
        status_start = start_datetime
        
        for entry in history:
            entry_created_at = _as_utc(entry.created_at)
            if current_status:
                duration = (entry_created_at - status_start).total_seconds()
                if current_status == "online":
                    online_seconds += duration
                else:
                    offline_seconds += duration
                    longest_offline = max(longest_offline, duration)
            
            if entry.status != current_status:
                if entry.status == "online" and current_status == "offline":
                    connection_count += 1
                current_status = entry.status
                status_start = entry_created_at
        
        # Ostatni okres do końca dnia
        if current_status:
            duration = (end_datetime - status_start).total_seconds()
            if current_status == "online":
                online_seconds += duration
            else:
                offline_seconds += duration
                longest_offline = max(longest_offline, duration)
        
        total_seconds = online_seconds + offline_seconds
        if total_seconds == 0:
            # Jeśli brak historii, sprawdź aktualny status
            if display.status == "online":
                online_seconds = 86400  # cały dzień
            else:
                offline_seconds = 86400
            total_seconds = 86400
        
        online_percentage = (online_seconds / total_seconds) * 100 if total_seconds > 0 else 0
        
        display_stats.append({
            "display_id": display.id,
            "display_name": display.name,
            "total_online_seconds": int(online_seconds),
            "total_offline_seconds": int(offline_seconds),
            "online_percentage": round(online_percentage, 2),
            "connection_count": connection_count,
            "longest_offline_seconds": int(longest_offline)
        })
        
        total_online += online_seconds
        total_offline += offline_seconds
    
    # Średni procent online
    total_time = total_online + total_offline
    average_online = (total_online / total_time * 100) if total_time > 0 else 0
    
    return {
        "date": report_date,
        "displays": display_stats,
        "total_displays": len(displays),
        "average_online_percentage": round(average_online, 2)
    }


def get_weekly_report(db: Session, week_start: date) -> Dict[str, Any]:
    """
    Generowanie raportu tygodniowego
    
    Args:
        db: Sesja bazy danych
        week_start: Data początku tygodnia (poniedziałek)
    
    Returns:
        Słownik z danymi raportu
    """
    week_end = week_start + timedelta(days=6)
    start_datetime = datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(week_end, datetime.max.time(), tzinfo=timezone.utc)
    
    displays = db.query(Display).all()
    
    display_stats = []
    total_online = 0
    total_offline = 0
    
    for display in displays:
        # Historia dla całego tygodnia
        history = db.query(DisplayStatusHistory).filter(
            and_(
                DisplayStatusHistory.display_id == display.id,
                DisplayStatusHistory.created_at >= start_datetime,
                DisplayStatusHistory.created_at <= end_datetime
            )
        ).order_by(DisplayStatusHistory.created_at).all()
        
        online_seconds = 0
        offline_seconds = 0
        connection_count = 0
        longest_offline = 0
        
        current_status = None
        status_start = start_datetime
        
        for entry in history:
            entry_created_at = _as_utc(entry.created_at)
            if current_status:
                duration = (entry_created_at - status_start).total_seconds()
                if current_status == "online":
                    online_seconds += duration
                else:
                    offline_seconds += duration
                    longest_offline = max(longest_offline, duration)
            
            if entry.status != current_status:
                if entry.status == "online" and current_status == "offline":
                    connection_count += 1
                current_status = entry.status
                status_start = entry_created_at
        
        # Ostatni okres do końca tygodnia
        if current_status:
            duration = (end_datetime - status_start).total_seconds()
            if current_status == "online":
                online_seconds += duration
            else:
                offline_seconds += duration
                longest_offline = max(longest_offline, duration)
        
        total_seconds = online_seconds + offline_seconds
        if total_seconds == 0:
            if display.status == "online":
                online_seconds = 7 * 86400  # cały tydzień
            else:
                offline_seconds = 7 * 86400
            total_seconds = 7 * 86400
        
        online_percentage = (online_seconds / total_seconds) * 100 if total_seconds > 0 else 0
        
        display_stats.append({
            "display_id": display.id,
            "display_name": display.name,
            "total_online_seconds": int(online_seconds),
            "total_offline_seconds": int(offline_seconds),
            "online_percentage": round(online_percentage, 2),
            "connection_count": connection_count,
            "longest_offline_seconds": int(longest_offline)
        })
        
        total_online += online_seconds
        total_offline += offline_seconds
    
    total_time = total_online + total_offline
    average_online = (total_online / total_time * 100) if total_time > 0 else 0
    
    return {
        "week_start": week_start,
        "week_end": week_end,
        "displays": display_stats,
        "total_displays": len(displays),
        "average_online_percentage": round(average_online, 2)
    }


def get_offline_report(
    db: Session,
    display_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Generowanie raportu offline dla wyświetlacza
    
    Args:
        db: Sesja bazy danych
        display_id: ID wyświetlacza
        start_date: Data początkowa
        end_date: Data końcowa
    
    Returns:
        Słownik z danymi raportu
    """
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        return None
    
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    
    # Historia statusów
    history = db.query(DisplayStatusHistory).filter(
        and_(
            DisplayStatusHistory.display_id == display_id,
            DisplayStatusHistory.created_at >= start_datetime,
            DisplayStatusHistory.created_at <= end_datetime
        )
    ).order_by(DisplayStatusHistory.created_at).all()
    
    incidents = []
    total_online = 0
    total_offline = 0
    
    current_status = None
    status_start = start_datetime
    
    for entry in history:
        entry_created_at = _as_utc(entry.created_at)
        if current_status:
            duration = (entry_created_at - status_start).total_seconds()
            if current_status == "offline":
                total_offline += duration
                incidents.append({
                    "start": status_start.isoformat(),
                    "end": entry_created_at.isoformat(),
                    "duration_seconds": int(duration),
                    "duration_hours": round(duration / 3600, 2)
                })
            else:
                total_online += duration
        
        if entry.status != current_status:
            current_status = entry.status
            status_start = entry_created_at
    
    # Ostatni okres
    if current_status:
        duration = (end_datetime - status_start).total_seconds()
        if current_status == "offline":
            total_offline += duration
            incidents.append({
                "start": status_start.isoformat(),
                "end": end_datetime.isoformat(),
                "duration_seconds": int(duration),
                "duration_hours": round(duration / 3600, 2)
            })
        else:
            total_online += duration
    
    total_time = total_online + total_offline
    if total_time == 0:
        total_time = ((end_date - start_date).days + 1) * 86400
    
    offline_percentage = (total_offline / total_time * 100) if total_time > 0 else 0
    
    return {
        "display_id": display.id,
        "display_name": display.name,
        "start_date": start_date,
        "end_date": end_date,
        "total_offline_seconds": int(total_offline),
        "total_online_seconds": int(total_online),
        "offline_percentage": round(offline_percentage, 2),
        "incidents": incidents
    }


def _as_utc(value: datetime) -> datetime:
    """Normalizes datetimes from DB to UTC-aware objects for safe arithmetic."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)



