"""
Serwis do zarządzania grupami wyświetlaczy
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.display import Display


def get_displays_for_group(db: Session, group_id: int) -> List[Display]:
    """Pobranie wyświetlaczy w grupie"""
    return db.query(Display).filter(Display.group_id == group_id).all()


def add_display_to_group(db: Session, display_id: int, group_id: int) -> Display:
    """Dodanie wyświetlacza do grupy"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if display:
        display.group_id = group_id
        db.commit()
        db.refresh(display)
    return display


def remove_display_from_group(db: Session, display_id: int) -> Display:
    """Usunięcie wyświetlacza z grupy"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if display:
        display.group_id = None
        db.commit()
        db.refresh(display)
    return display


def validate_group_type(group_type: str, display_count: int) -> tuple[bool, str]:
    """
    Walidacja typu grupy względem liczby wyświetlaczy
    
    Returns:
        (is_valid, error_message)
    """
    # "single" nigdy nie moze miec wiecej niz 1 wyswietlacza.
    if group_type == "single" and display_count > 1:
        return False, "Group type 'single' supports at most 1 display"

    # Pozostale typy grup dopuszczaja etapowe budowanie (1, 2, ... wyswietlaczy).
    # To pozwala dodac pierwszy wyswietlacz, a dopiero potem kolejne.
    if group_type in {"vertical", "horizontal", "mixed"} and display_count < 1:
        return False, f"Group type '{group_type}' requires at least 1 display"
    
    return True, ""

