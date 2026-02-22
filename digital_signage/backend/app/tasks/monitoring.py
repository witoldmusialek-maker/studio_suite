"""
Zadania monitoringu wyswietlaczy
"""
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.alert_service import check_and_create_connection_alerts
from app.services.display_service import check_offline_displays, mark_display_offline


@celery_app.task(name="app.tasks.monitoring.check_displays_offline")
def check_displays_offline():
    """
    Zadanie do sprawdzania wyswietlaczy offline i tworzenia alertow.
    Uruchamiane przez Celery Beat co minute.
    """
    db: Session = SessionLocal()
    try:
        # Sprawdzenie wyswietlaczy offline (brak heartbeat > 1 minuta)
        offline_displays = check_offline_displays(db, timeout_minutes=1)

        for display in offline_displays:
            mark_display_offline(db, display.id)
            print(f"Wyswietlacz {display.name} (ID: {display.id}) oznaczony jako offline")

        # Sprawdzenie i utworzenie alertow
        alerts_created = check_and_create_connection_alerts(db)

        return {
            "offline_displays": len(offline_displays),
            "alerts_created": alerts_created,
        }
    finally:
        db.close()