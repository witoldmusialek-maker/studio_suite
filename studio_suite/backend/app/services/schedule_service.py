"""
Serwis do zarządzania harmonogramami
"""
from datetime import datetime, time, date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.models.display import Display


def get_active_schedules_for_display(
    db: Session,
    display_id: int,
    current_datetime: Optional[datetime] = None
) -> List[Schedule]:
    """
    Pobranie aktywnych harmonogramów dla wyświetlacza w danym czasie
    
    Args:
        db: Sesja bazy danych
        display_id: ID wyświetlacza
        current_datetime: Aktualna data i czas (domyślnie teraz)
    
    Returns:
        Lista aktywnych harmonogramów
    """
    if current_datetime is None:
        current_datetime = datetime.now()
    
    current_time = current_datetime.time()
    current_date = current_datetime.date()
    current_weekday = current_datetime.weekday() + 1  # 1=poniedziałek, 7=niedziela
    
    # Pobranie harmonogramów dla wyświetlacza
    schedules = db.query(Schedule).filter(
        Schedule.display_id == display_id,
        Schedule.active == True,
        Schedule.start_time <= current_time,
        Schedule.end_time >= current_time
    ).all()
    
    # Filtrowanie po datach i dniach tygodnia
    active_schedules = []
    for schedule in schedules:
        # Sprawdzenie dat
        if schedule.start_date and current_date < schedule.start_date:
            continue
        if schedule.end_date and current_date > schedule.end_date:
            continue
        
        # Sprawdzenie dni tygodnia
        if schedule.days_of_week and current_weekday not in schedule.days_of_week:
            continue
        
        active_schedules.append(schedule)
    
    # Sortowanie po priorytecie (wyższy priorytet = wyższa wartość)
    active_schedules.sort(key=lambda x: x.priority, reverse=True)
    
    return active_schedules


def get_current_content_for_display(
    db: Session,
    display_id: int,
    current_datetime: Optional[datetime] = None
) -> Optional[int]:
    """
    Pobranie ID treści do wyświetlenia dla wyświetlacza w danym czasie
    
    Returns:
        ID treści lub None jeśli brak harmonogramu
    """
    schedules = get_active_schedules_for_display(db, display_id, current_datetime)
    
    if not schedules:
        return None
    
    # Zwróć treść z harmonogramu o najwyższym priorytecie
    return schedules[0].content_id


def get_schedules_for_group(
    db: Session,
    group_id: int
) -> List[Schedule]:
    """Pobranie harmonogramów dla grupy wyświetlaczy"""
    return db.query(Schedule).filter(
        Schedule.group_id == group_id,
        Schedule.active == True
    ).all()

