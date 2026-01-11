"""
Zadania monitoringu wyświetlaczy
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.display_service import check_offline_displays, mark_display_offline
from app.services.alert_service import check_and_create_connection_alerts


def check_displays_offline():
    """
    Zadanie do sprawdzania wyświetlaczy offline i tworzenia alertów
    Powinno być uruchamiane przez Celery Beat co minutę
    """
    db: Session = SessionLocal()
    try:
        # Sprawdzenie wyświetlaczy offline (brak heartbeat > 1 minuta)
        offline_displays = check_offline_displays(db, timeout_minutes=1)
        
        for display in offline_displays:
            mark_display_offline(db, display.id)
            print(f"Wyświetlacz {display.name} (ID: {display.id}) oznaczony jako offline")
        
        # Sprawdzenie i utworzenie alertów
        alerts_created = check_and_create_connection_alerts(db)
        
        return {
            "offline_displays": len(offline_displays),
            "alerts_created": alerts_created
        }
    finally:
        db.close()

