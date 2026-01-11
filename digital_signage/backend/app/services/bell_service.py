"""
Serwis do zarządzania dzwonkami szkolnymi
"""
from datetime import datetime, time, date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.bell_schedule import BellSchedule
from app.models.bell_history import BellHistory
from app.models.display import Display


def get_bells_to_play(db: Session, current_time: Optional[time] = None) -> List[BellSchedule]:
    """
    Pobranie dzwonków do odtworzenia w danym czasie
    
    Args:
        db: Sesja bazy danych
        current_time: Aktualny czas (domyślnie teraz)
    
    Returns:
        Lista harmonogramów dzwonków do odtworzenia
    """
    if current_time is None:
        current_time = datetime.now().time()
    
    current_date = datetime.now().date()
    current_weekday = datetime.now().weekday() + 1  # 1=poniedziałek, 7=niedziela
    
    # Pobranie aktywnych harmonogramów dla tego czasu (z tolerancją ±1 minuta)
    from sqlalchemy import and_, or_
    
    # Sprawdzenie czy czas jest w zakresie ±1 minuta od bell_time
    bells = db.query(BellSchedule).filter(
        BellSchedule.active == True,
        BellSchedule.play_on_displays == True
    ).all()
    
    bells_to_play = []
    for bell in bells:
        # Sprawdzenie czasu (z tolerancją ±1 minuta)
        bell_time_seconds = bell.bell_time.hour * 3600 + bell.bell_time.minute * 60 + bell.bell_time.second
        current_time_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        
        time_diff = abs(current_time_seconds - bell_time_seconds)
        if time_diff > 60:  # Więcej niż 1 minuta różnicy
            continue
        
        # Sprawdzenie dat
        if bell.start_date and current_date < bell.start_date:
            continue
        if bell.end_date and current_date > bell.end_date:
            continue
        
        # Sprawdzenie dni tygodnia
        if bell.days_of_week and current_weekday not in bell.days_of_week:
            continue
        
        bells_to_play.append(bell)
    
    return bells_to_play


def log_bell_play(
    db: Session,
    bell_schedule_id: int,
    status: str = "success",
    error_message: Optional[str] = None
) -> BellHistory:
    """Zapisanie historii odtworzenia dzwonka"""
    history = BellHistory(
        bell_schedule_id=bell_schedule_id,
        played_at=datetime.utcnow(),
        status=status,
        error_message=error_message
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_displays_for_bell(db: Session, bell: BellSchedule) -> List[Display]:
    """Pobranie wyświetlaczy dla dzwonka"""
    if bell.display_ids:
        # Konkretne wyświetlacze
        return db.query(Display).filter(Display.id.in_(bell.display_ids)).all()
    else:
        # Wszystkie wyświetlacze
        return db.query(Display).filter(Display.status == "online").all()



