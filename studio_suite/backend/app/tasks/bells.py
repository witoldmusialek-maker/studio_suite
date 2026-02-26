"""
Zadania zwiazane z dzwonkami szkolnymi
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.bell_history import BellHistory
from app.services.bell_service import get_bells_to_play, get_displays_for_bell, log_bell_play
from app.services.server_audio_service import play_bell_on_server


@celery_app.task(name="app.tasks.bells.check_and_play_bells")
def check_and_play_bells():
    """
    Sprawdzenie harmonogramu dzwonkow i ewentualne lokalne odtworzenie na serwerze.
    Uruchamiane przez Celery Beat co minute.
    """
    db: Session = SessionLocal()
    try:
        bells = get_bells_to_play(db)

        server_played = 0
        server_failed = 0
        skipped = 0
        for bell in bells:
            # Prevent duplicate processing in one-minute window.
            recent_play = db.query(BellHistory).filter(
                BellHistory.bell_schedule_id == bell.id,
                BellHistory.played_at >= datetime.utcnow() - timedelta(minutes=1),
            ).first()
            if recent_play:
                skipped += 1
                continue

            # Optional local playback on server (e.g. T620 + radiowezel).
            if settings.BELL_SERVER_PLAYBACK_ENABLED:
                ok, message = play_bell_on_server(bell.sound_file_path or "", bell.volume or 50)
                if ok:
                    log_bell_play(db, bell.id, status="played_server")
                    server_played += 1
                else:
                    log_bell_play(db, bell.id, status="failed_server", error_message=message)
                    server_failed += 1

        return {
            "bells_found": len(bells),
            "server_played": server_played,
            "server_failed": server_failed,
            "skipped_recent": skipped,
        }
    finally:
        db.close()
