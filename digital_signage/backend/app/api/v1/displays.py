"""
Endpointy API dla wyświetlaczy
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.display import Display
from app.models.user import User, UserRole
from app.api.deps import get_current_user, get_current_admin
from app.schemas.display import (
    DisplayCreate,
    DisplayUpdate,
    DisplayRegister,
    DisplayHeartbeat,
    DisplayResponse,
    DisplayStatusResponse
)

router = APIRouter(prefix="/displays", tags=["displays"])


def _display_name_prefix(width: int, height: int) -> str:
    # Audio-only clients register as 1x1 "virtual display".
    return "Bell" if width == 1 and height == 1 else "Display"


@router.post("/register", response_model=DisplayResponse, status_code=status.HTTP_201_CREATED)
async def register_display(
    display_data: DisplayRegister,
    db: Session = Depends(get_db)
):
    """Rejestracja wyświetlacza przez MAC address"""
    # Sprawdzenie czy wyświetlacz już istnieje
    existing_display = db.query(Display).filter(
        Display.mac_address == display_data.mac_address
    ).first()
    
    if existing_display:
        # Aktualizacja danych
        existing_display.ip_address = display_data.ip_address
        existing_display.resolution_width = display_data.resolution_width
        existing_display.resolution_height = display_data.resolution_height
        expected_prefix = _display_name_prefix(display_data.resolution_width, display_data.resolution_height)
        # Keep custom names, but normalize auto-generated legacy names.
        if existing_display.name.startswith("Display-") or existing_display.name.startswith("Bell-"):
            existing_display.name = f"{expected_prefix}-{display_data.mac_address[-6:]}"
        existing_display.status = "online"
        existing_display.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(existing_display)
        return existing_display
    
    # Utworzenie nowego wyświetlacza
    name_prefix = _display_name_prefix(display_data.resolution_width, display_data.resolution_height)
    db_display = Display(
        name=f"{name_prefix}-{display_data.mac_address[-6:]}",
        mac_address=display_data.mac_address,
        ip_address=display_data.ip_address,
        resolution_width=display_data.resolution_width,
        resolution_height=display_data.resolution_height,
        status="online",
        last_seen=datetime.utcnow()
    )
    db.add(db_display)
    db.commit()
    db.refresh(db_display)
    return db_display


@router.post("/{display_id}/heartbeat", status_code=status.HTTP_200_OK)
async def heartbeat(
    display_id: int,
    heartbeat_data: DisplayHeartbeat,
    db: Session = Depends(get_db)
):
    """Heartbeat od wyświetlacza - aktualizacja statusu"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    # Sprawdzenie czy status zmieniał się z offline na online
    was_offline = display.status == "offline"
    
    # Aktualizacja statusu
    display.status = "online"
    display.last_seen = datetime.utcnow()
    db.commit()
    
    # Jeśli przywrócono połączenie, utwórz alert
    if was_offline:
        from app.services.alert_service import create_connection_restored_alert
        create_connection_restored_alert(db, display_id)
    
    return {"status": "ok", "message": "Heartbeat received"}


@router.get("/", response_model=List[DisplayResponse])
async def get_displays(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    floor_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy wyświetlaczy (admin i operator)"""
    query = db.query(Display)
    
    if status_filter:
        query = query.filter(Display.status == status_filter)
    if floor_filter:
        query = query.filter(Display.floor == floor_filter)
    
    displays = query.offset(skip).limit(limit).all()
    return displays


@router.get("/{display_id}", response_model=DisplayResponse)
async def get_display(
    display_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów wyświetlacza"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    return display


@router.get("/{display_id}/status", response_model=DisplayStatusResponse)
async def get_display_status(
    display_id: int,
    db: Session = Depends(get_db)
):
    """Pobranie statusu wyświetlacza (publiczny endpoint dla klienta)"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    return DisplayStatusResponse(
        id=display.id,
        name=display.name,
        status=display.status,
        last_seen=display.last_seen,
        floor=display.floor,
        group_id=display.group_id
    )


@router.post("/", response_model=DisplayResponse, status_code=status.HTTP_201_CREATED)
async def create_display(
    display_data: DisplayCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Utworzenie wyświetlacza (tylko admin)"""
    # Sprawdzenie czy MAC address już istnieje
    existing = db.query(Display).filter(
        Display.mac_address == display_data.mac_address
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display with this MAC address already exists"
        )
    
    db_display = Display(**display_data.dict())
    db.add(db_display)
    db.commit()
    db.refresh(db_display)
    return db_display


@router.put("/{display_id}", response_model=DisplayResponse)
async def update_display(
    display_id: int,
    display_data: DisplayUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja wyświetlacza (tylko admin)"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    update_data = display_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(display, field, value)
    
    db.commit()
    db.refresh(display)
    return display


@router.delete("/{display_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_display(
    display_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie wyświetlacza (tylko admin)"""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    db.delete(display)
    db.commit()
    return None


# In-memory storage for test content (simple solution for testing)
_test_content = {}

@router.post("/{display_id}/test-content/{content_id}")
async def send_test_content(
    display_id: int,
    content_id: int,
    db: Session = Depends(get_db)
):
    """Wyślij treść testową do wyświetlacza"""
    from app.models.content import Content
    
    # Sprawdź czy wyświetlacz istnieje
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")
    
    # Sprawdź czy treść istnieje
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Zapisz test content dla tego wyświetlacza
    _test_content[display_id] = {
        "content_id": content_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return {"status": "ok", "message": f"Content {content_id} sent to display {display_id}"}


@router.get("/{display_id}/test-content")
async def get_test_content(
    display_id: int,
    db: Session = Depends(get_db)
):
    """Pobierz treść testową dla wyświetlacza (endpoint dla klienta)"""
    from app.models.content import Content
    from app.schemas.content import ContentResponse
    
    # Sprawdź czy wyświetlacz istnieje
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")
    
    # Sprawdź czy jest test content
    test_data = _test_content.get(display_id)
    if not test_data:
        return {"content": None}
    
    # Pobierz treść
    content = db.query(Content).filter(Content.id == test_data["content_id"]).first()
    if not content:
        return {"content": None}
    
    return {
        "content": {
            "id": content.id,
            "name": content.original_filename,
            "type": content.type,
            "file_path": content.file_path,
            "file_size": float(content.file_size_mb) if content.file_size_mb else None,
            "mime_type": None,
            "duration": content.duration_seconds,
            "width": None,
            "height": None,
            "thumbnail": content.thumbnail_path,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "updated_at": content.updated_at.isoformat() if content.updated_at else None
        },
        "timestamp": test_data["timestamp"]
    }


@router.delete("/{display_id}/test-content")
async def clear_test_content(
    display_id: int,
    db: Session = Depends(get_db)
):
    """Wyczyść treść testową"""
    if display_id in _test_content:
        del _test_content[display_id]
    return {"status": "ok"}
