"""
Zadania związane z dzwonkami szkolnymi
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.bell_history import BellHistory
from app.services.bell_service import get_bells_to_play, get_displays_for_bell, log_bell_play


def check_and_play_bells():
    """
    Sprawdzenie harmonogramu dzwonków i oznaczenie do odtworzenia
    Powinno być uruchamiane przez Celery Beat co minutę
    """
    db: Session = SessionLocal()
    try:
        bells = get_bells_to_play(db)
        
        played_count = 0
        for bell in bells:
            displays = get_displays_for_bell(db, bell)
            
            if displays and bell.sound_file_path:
                # Sprawdzenie czy dzwonek nie był już odtworzony w ciągu ostatniej minuty
                recent_play = db.query(BellHistory).filter(
                    BellHistory.bell_schedule_id == bell.id,
                    BellHistory.played_at >= datetime.utcnow() - timedelta(minutes=1)
                ).first()
                
                if not recent_play:
                    # Zapisanie historii (status będzie ustawiony przez klienta po odtworzeniu)
                    log_bell_play(db, bell.id, status="pending")
                    played_count += 1
                    print(f"Dzwonek {bell.name} (ID: {bell.id}) oznaczony do odtworzenia na {len(displays)} wyświetlaczach")
        
        return {
            "bells_found": len(bells),
            "bells_played": played_count
        }
    finally:
        db.close()

