"""
Prosta, czytelna logika schedulera dzwonkow.

Modul celowo trzyma "czysta" logike wyboru:
1. Wyznacz aktywny profil
2. Odfiltruj dzwonki do profilu
3. Sprawdz warunki czasu/daty/dnia tygodnia
"""
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.bell_profile import BellProfile, BellProfileOverride, BellScheduleProfile
from app.models.bell_schedule import BellSchedule
from app.utils.time_utils import local_now


@dataclass(frozen=True)
class BellContext:
    now: datetime
    current_date: date
    current_time: time
    current_weekday: int  # 1=poniedzialek, 7=niedziela


def build_bell_context(
    now: Optional[datetime] = None,
    current_time: Optional[time] = None,
) -> BellContext:
    if now is None:
        now = local_now()
    return BellContext(
        now=now,
        current_date=now.date(),
        current_time=current_time or now.time(),
        current_weekday=now.weekday() + 1,
    )


def resolve_active_profile(db: Session, now: Optional[datetime] = None) -> Optional[BellProfile]:
    if now is None:
        now = local_now()

    override = db.query(BellProfileOverride).filter(BellProfileOverride.day == now.date()).first()
    if override:
        profile = db.query(BellProfile).filter(BellProfile.id == override.profile_id).first()
        if profile and profile.is_active:
            return profile

    month_profile = db.query(BellProfile).filter(
        BellProfile.month == now.month,
        BellProfile.is_active == True,  # noqa: E712
    ).first()
    if month_profile:
        return month_profile

    return db.query(BellProfile).filter(
        BellProfile.is_default == True,  # noqa: E712
        BellProfile.is_active == True,  # noqa: E712
    ).first()


def filter_bells_for_profile(
    db: Session,
    bells: List[BellSchedule],
    active_profile: Optional[BellProfile],
) -> List[BellSchedule]:
    if not bells:
        return bells

    links = db.query(BellScheduleProfile).all()
    if not links:
        return bells

    by_schedule: Dict[int, List[int]] = {}
    for link in links:
        by_schedule.setdefault(link.bell_schedule_id, []).append(link.profile_id)

    allowed_profile_id = active_profile.id if active_profile else None
    is_default_context = bool(active_profile and active_profile.is_default)

    filtered: List[BellSchedule] = []
    for bell in bells:
        bell_profiles = by_schedule.get(bell.id, [])
        if not bell_profiles:
            if allowed_profile_id is None or is_default_context:
                filtered.append(bell)
            continue

        if allowed_profile_id and allowed_profile_id in bell_profiles:
            filtered.append(bell)

    return filtered


def is_bell_due_now(
    bell: BellSchedule,
    context: BellContext,
    tolerance_seconds: int = 60,
) -> bool:
    bell_time_seconds = (
        bell.bell_time.hour * 3600 + bell.bell_time.minute * 60 + bell.bell_time.second
    )
    current_time_seconds = (
        context.current_time.hour * 3600
        + context.current_time.minute * 60
        + context.current_time.second
    )
    if abs(current_time_seconds - bell_time_seconds) > tolerance_seconds:
        return False

    if bell.start_date and context.current_date < bell.start_date:
        return False
    if bell.end_date and context.current_date > bell.end_date:
        return False

    if bell.days_of_week and context.current_weekday not in bell.days_of_week:
        return False

    return True

