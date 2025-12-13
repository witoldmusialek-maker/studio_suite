"""
Zadania monitoringu wyświetlaczy
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.display_service import check_offline_displays, mark_display_offline


def check_displays_offline():
    """
    Zadanie do sprawdzania wyświetlaczy offline
    Powinno być uruchamiane przez Celery Beat co minutę
    """
    db: Session = SessionLocal()
    try:
        # Sprawdzenie wyświetlaczy offline (brak heartbeat > 1 minuta)
        offline_displays = check_offline_displays(db, timeout_minutes=1)
        
        for display in offline_displays:
            mark_display_offline(db, display.id)
            print(f"Wyświetlacz {display.name} (ID: {display.id}) oznaczony jako offline")
        
        return len(offline_displays)
    finally:
        db.close()

