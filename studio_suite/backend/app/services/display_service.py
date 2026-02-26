"""
Serwis do zarządzania wyświetlaczami - logika biznesowa
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List

from app.models.display import Display


def check_offline_displays(db: Session, timeout_minutes: int = 1) -> List[Display]:
    """
    Sprawdzenie wyświetlaczy, które nie wysłały heartbeat przez określony czas
    Zwraca listę wyświetlaczy, które powinny być oznaczone jako offline
    """
    timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
    
    # Wyświetlacze online, które nie wysłały heartbeat
    offline_displays = db.query(Display).filter(
        Display.status == "online",
        (Display.last_seen < timeout_threshold) | (Display.last_seen.is_(None))
    ).all()
    
    return offline_displays


def mark_display_offline(db: Session, display_id: int) -> Display:
    """Oznaczenie wyświetlacza jako offline"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if display and display.status == "online":
        display.status = "offline"
        db.commit()
        db.refresh(display)
    return display


def mark_display_online(db: Session, display_id: int) -> Display:
    """Oznaczenie wyświetlacza jako online"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if display:
        display.status = "online"
        display.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(display)
    return display


def get_display_by_mac(db: Session, mac_address: str) -> Display:
    """Pobranie wyświetlacza po MAC address"""
    return db.query(Display).filter(Display.mac_address == mac_address).first()

