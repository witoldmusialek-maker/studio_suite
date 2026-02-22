"""
Service for break music playlist selection.
"""
from datetime import datetime, time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bell_music import BellMusicSchedule, BellMusicTrack
from app.services.bell_service import is_bell_playback_blocked, get_active_bell_profile
from app.utils.time_utils import local_now


def get_active_music_schedule(
    db: Session,
    display_id: Optional[int] = None,
    now: Optional[datetime] = None,
    ignore_runtime_block: bool = False,
) -> Optional[BellMusicSchedule]:
    if now is None:
        now = local_now()

    if not ignore_runtime_block and is_bell_playback_blocked(db, now):
        return None

    current_date = now.date()
    current_weekday = now.weekday() + 1  # 1=Monday
    current_time = now.time()
    active_profile = get_active_bell_profile(db, now)
    active_profile_id = active_profile.id if active_profile else None

    candidates = (
        db.query(BellMusicSchedule)
        .filter(BellMusicSchedule.active == True)  # noqa: E712
        .order_by(BellMusicSchedule.priority.desc(), BellMusicSchedule.start_time.asc())
        .all()
    )

    for schedule in candidates:
        if schedule.start_date and current_date < schedule.start_date:
            continue
        if schedule.end_date and current_date > schedule.end_date:
            continue

        if schedule.days_of_week and current_weekday not in schedule.days_of_week:
            continue

        if display_id and schedule.display_ids and display_id not in schedule.display_ids:
            continue

        if schedule.profile_ids:
            if not active_profile_id or active_profile_id not in schedule.profile_ids:
                continue

        if not _is_time_between(current_time, schedule.start_time, schedule.end_time):
            continue

        return schedule

    return None


def get_active_music_tracks(db: Session, schedule_id: int) -> List[BellMusicTrack]:
    return (
        db.query(BellMusicTrack)
        .filter(
            BellMusicTrack.schedule_id == schedule_id,
            BellMusicTrack.active == True,  # noqa: E712
        )
        .order_by(BellMusicTrack.sort_order.asc(), BellMusicTrack.id.asc())
        .all()
    )


def _is_time_between(value: time, start: time, end: time) -> bool:
    # Typical school breaks do not cross midnight, but this keeps behavior safe.
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end
