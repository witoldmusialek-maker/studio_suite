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
        existing_display.status = "online"
        existing_display.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(existing_display)
        return existing_display
    
    # Utworzenie nowego wyświetlacza
    db_display = Display(
        name=f"Display-{display_data.mac_address[-6:]}",
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
    
    # Aktualizacja statusu
    display.status = "online"
    display.last_seen = datetime.utcnow()
    db.commit()
    
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

