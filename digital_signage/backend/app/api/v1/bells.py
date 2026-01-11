"""
Endpointy API dla dzwonków szkolnych
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.bell_schedule import BellSchedule
from app.models.bell_history import BellHistory
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.bell import (
    BellScheduleCreate,
    BellScheduleUpdate,
    BellScheduleResponse,
    BellHistoryResponse,
    BellPlayCommand
)
from app.services.bell_service import get_displays_for_bell, log_bell_play
from app.config import settings
import os
import shutil

router = APIRouter(prefix="/bells", tags=["bells"])


@router.post("/upload-sound", status_code=status.HTTP_201_CREATED)
async def upload_bell_sound(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload pliku dźwiękowego dla dzwonka (tylko admin)"""
    # Walidacja typu pliku
    allowed_types = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nieobsługiwany typ pliku audio: {file.content_type}"
        )
    
    # Walidacja rozmiaru (max 5 MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plik dźwiękowy jest za duży (max 5 MB)"
        )
    
    # Zapis pliku
    sounds_dir = os.path.join(settings.CONTENT_DIR, "sounds")
    os.makedirs(sounds_dir, exist_ok=True)
    
    filename = file.filename
    file_path = os.path.join(sounds_dir, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return {
        "filename": filename,
        "file_path": file_path,
        "size_bytes": len(content)
    }


@router.post("/", response_model=BellScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_bell_schedule(
    bell_data: BellScheduleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Utworzenie harmonogramu dzwonka (tylko admin)"""
    db_bell = BellSchedule(**bell_data.dict())
    db.add(db_bell)
    db.commit()
    db.refresh(db_bell)
    return db_bell


@router.get("/", response_model=List[BellScheduleResponse])
async def get_bell_schedules(
    skip: int = 0,
    limit: int = 100,
    active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy harmonogramów dzwonków (admin i operator)"""
    query = db.query(BellSchedule)
    
    if active is not None:
        query = query.filter(BellSchedule.active == active)
    
    bells = query.order_by(BellSchedule.bell_time).offset(skip).limit(limit).all()
    return bells


@router.get("/{bell_id}", response_model=BellScheduleResponse)
async def get_bell_schedule(
    bell_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów harmonogramu dzwonka"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    return bell


@router.put("/{bell_id}", response_model=BellScheduleResponse)
async def update_bell_schedule(
    bell_id: int,
    bell_data: BellScheduleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja harmonogramu dzwonka (tylko admin)"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    update_data = bell_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bell, field, value)
    
    db.commit()
    db.refresh(bell)
    return bell


@router.delete("/{bell_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bell_schedule(
    bell_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie harmonogramu dzwonka (tylko admin)"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    # Usunięcie pliku dźwiękowego jeśli istnieje
    if bell.sound_file_path and os.path.exists(bell.sound_file_path):
        os.remove(bell.sound_file_path)
    
    db.delete(bell)
    db.commit()
    return None


@router.get("/{bell_id}/history", response_model=List[BellHistoryResponse])
async def get_bell_history(
    bell_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie historii odtworzeń dzwonka"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    history = db.query(BellHistory).filter(
        BellHistory.bell_schedule_id == bell_id
    ).order_by(BellHistory.played_at.desc()).limit(limit).all()
    
    return history


@router.get("/display/{display_id}/play-command", response_model=Optional[BellPlayCommand])
async def get_bell_play_command(
    display_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobranie komendy odtwarzania dzwonka dla wyświetlacza (publiczny endpoint dla klienta)
    Sprawdza czy jest dzwonek do odtworzenia w tym momencie
    """
    from app.services.bell_service import get_bells_to_play
    
    bells = get_bells_to_play(db)
    
    for bell in bells:
        displays = get_displays_for_bell(db, bell)
        display_ids = [d.id for d in displays]
        
        if display_id in display_ids:
            # Sprawdzenie czy dzwonek nie był już odtworzony w ciągu ostatniej minuty
            recent_play = db.query(BellHistory).filter(
                BellHistory.bell_schedule_id == bell.id,
                BellHistory.played_at >= datetime.utcnow() - datetime.timedelta(minutes=1)
            ).first()
            
            if not recent_play and bell.sound_file_path:
                return BellPlayCommand(
                    bell_schedule_id=bell.id,
                    sound_file_path=bell.sound_file_path,
                    volume=bell.volume
                )
    
    return None

