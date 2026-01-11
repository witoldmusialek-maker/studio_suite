"""
Serwis do zarządzania alertami
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.display_status_history import DisplayStatusHistory
from app.models.display import Display


def create_alert(
    db: Session,
    display_id: int,
    alert_type: str,
    severity: str,
    message: str
) -> Alert:
    """Utworzenie alertu"""
    alert = Alert(
        display_id=display_id,
        alert_type=alert_type,
        severity=severity,
        message=message
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(
    db: Session,
    alert_id: int,
    resolved_by: Optional[int] = None
) -> Alert:
    """Oznaczenie alertu jako rozwiązany"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        if resolved_by:
            alert.resolved_by = resolved_by
        db.commit()
        db.refresh(alert)
    return alert


def check_and_create_connection_alerts(db: Session):
    """
    Sprawdzenie wyświetlaczy i utworzenie alertów dla braku komunikacji
    Powinno być uruchamiane przez Celery Beat co minutę
    """
    from app.services.display_service import check_offline_displays
    
    # Sprawdzenie wyświetlaczy offline (brak heartbeat > 1 minuta)
    offline_displays = check_offline_displays(db, timeout_minutes=1)
    
    alerts_created = 0
    for display in offline_displays:
        # Sprawdzenie czy już istnieje aktywny alert dla tego wyświetlacza
        existing_alert = db.query(Alert).filter(
            Alert.display_id == display.id,
            Alert.alert_type == "connection_lost",
            Alert.resolved == False
        ).first()
        
        if not existing_alert:
            # Obliczenie czasu offline
            if display.last_seen:
                offline_duration = (datetime.utcnow() - display.last_seen).total_seconds()
            else:
                offline_duration = 0
            
            # Określenie severity na podstawie czasu offline
            if offline_duration > 1800:  # > 30 minut
                severity = "critical"
            elif offline_duration > 300:  # > 5 minut
                severity = "error"
            else:
                severity = "warning"
            
            # Utworzenie alertu
            create_alert(
                db=db,
                display_id=display.id,
                alert_type="connection_lost",
                severity=severity,
                message=f"Wyświetlacz {display.name} nie odpowiada od {int(offline_duration)} sekund"
            )
            alerts_created += 1
            
            # Zapisanie historii statusu
            save_status_history(db, display.id, "offline", display.last_seen)
    
    return alerts_created


def create_connection_restored_alert(
    db: Session,
    display_id: int
) -> Alert:
    """Utworzenie alertu o przywróceniu połączenia"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        return None
    
    # Rozwiązanie starych alertów connection_lost
    old_alerts = db.query(Alert).filter(
        Alert.display_id == display_id,
        Alert.alert_type == "connection_lost",
        Alert.resolved == False
    ).all()
    
    for alert in old_alerts:
        resolve_alert(db, alert.id)
    
    # Utworzenie alertu o przywróceniu
    alert = create_alert(
        db=db,
        display_id=display_id,
        alert_type="connection_restored",
        severity="info",
        message=f"Wyświetlacz {display.name} przywrócił połączenie"
    )
    
    # Zapisanie historii statusu
    save_status_history(db, display_id, "online", datetime.utcnow())
    
    return alert


def save_status_history(
    db: Session,
    display_id: int,
    status: str,
    last_seen: Optional[datetime] = None
):
    """Zapisanie historii statusu wyświetlacza"""
    # Pobranie ostatniego rekordu historii
    last_history = db.query(DisplayStatusHistory).filter(
        DisplayStatusHistory.display_id == display_id
    ).order_by(DisplayStatusHistory.created_at.desc()).first()
    
    # Jeśli status się zmienił z online na offline
    if status == "offline" and last_history and last_history.status == "online":
        history = DisplayStatusHistory(
            display_id=display_id,
            status=status,
            last_seen=last_seen,
            connection_lost_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    # Jeśli status się zmienił z offline na online
    elif status == "online" and last_history and last_history.status == "offline":
        # Aktualizacja ostatniego rekordu offline
        if last_history.connection_lost_at:
            duration_offline = (datetime.utcnow() - last_history.connection_lost_at).total_seconds()
            last_history.duration_offline_seconds = int(duration_offline)
            last_history.connection_restored_at = datetime.utcnow()
            db.commit()
        
        # Nowy rekord online
        history = DisplayStatusHistory(
            display_id=display_id,
            status=status,
            last_seen=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    else:
        # Nowy rekord dla tego samego statusu (aktualizacja czasu)
        history = DisplayStatusHistory(
            display_id=display_id,
            status=status,
            last_seen=last_seen or datetime.utcnow()
        )
        db.add(history)
        db.commit()



