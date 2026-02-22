"""
Serwis do zarzadzania dzwonkami szkolnymi.

Uproszczony przeplyw (na wzor prostszego projektu):
1. Sprawdz blokady runtime
2. Pobierz aktywne dzwonki-kandydaty
3. Wyznacz aktywny profil
4. Odfiltruj dzwonki po profilu
5. Zostaw tylko dzwonki "na teraz"
"""
from datetime import datetime, time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bell_history import BellHistory
from app.models.bell_profile import BellProfile
from app.models.bell_runtime import BellCalendarOverride, BellRuntimeControl
from app.models.bell_schedule import BellSchedule
from app.models.display import Display
from app.services.bell_scheduler_logic import (
    build_bell_context,
    filter_bells_for_profile,
    is_bell_due_now,
    resolve_active_profile,
)
from app.utils.time_utils import local_now


def get_bells_to_play(db: Session, current_time: Optional[time] = None) -> List[BellSchedule]:
    """
    Zwraca dzwonki do odtworzenia dla biezacej chwili.
    """
    context = build_bell_context(now=local_now(), current_time=current_time)

    if is_bell_playback_blocked(db, context.now):
        return []

    candidate_bells = db.query(BellSchedule).filter(
        BellSchedule.active == True,  # noqa: E712
        BellSchedule.play_on_displays == True,  # noqa: E712
    ).all()

    active_profile = resolve_active_profile(db, context.now)
    filtered_bells = filter_bells_for_profile(db, candidate_bells, active_profile)
    return [bell for bell in filtered_bells if is_bell_due_now(bell, context)]


def log_bell_play(
    db: Session,
    bell_schedule_id: int,
    status: str = "success",
    error_message: Optional[str] = None,
) -> BellHistory:
    """Zapisanie historii odtworzenia dzwonka."""
    history = BellHistory(
        bell_schedule_id=bell_schedule_id,
        played_at=datetime.utcnow(),
        status=status,
        error_message=error_message,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_displays_for_bell(db: Session, bell: BellSchedule) -> List[Display]:
    """Pobranie wyswietlaczy dla dzwonka."""
    if bell.display_ids:
        return db.query(Display).filter(Display.id.in_(bell.display_ids)).all()
    return db.query(Display).filter(Display.status == "online").all()


def get_or_create_runtime_control(db: Session) -> BellRuntimeControl:
    control = db.query(BellRuntimeControl).first()
    if control:
        return control
    control = BellRuntimeControl(bells_enabled=True)
    db.add(control)
    db.commit()
    db.refresh(control)
    return control


def is_bell_playback_blocked(db: Session, now: Optional[datetime] = None) -> bool:
    if now is None:
        now = local_now()

    control = get_or_create_runtime_control(db)
    if not control.bells_enabled:
        return True
    if control.pause_until and control.pause_until > now:
        return True

    day_override = db.query(BellCalendarOverride).filter(BellCalendarOverride.day == now.date()).first()
    if day_override and not day_override.bells_enabled:
        return True

    return False


def get_active_bell_profile(db: Session, now: Optional[datetime] = None) -> Optional[BellProfile]:
    """Alias zachowany dla zgodnosci z API i innymi serwisami."""
    return resolve_active_profile(db, now)

