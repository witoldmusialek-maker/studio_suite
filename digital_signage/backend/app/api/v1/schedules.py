"""
Endpointy API dla harmonogramów
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.schedule import Schedule
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleForDisplay
)
from app.services.schedule_service import (
    get_active_schedules_for_display,
    get_current_content_for_display
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Utworzenie harmonogramu (tylko admin)"""
    # Walidacja: display_id lub group_id musi być podane
    if not schedule_data.display_id and not schedule_data.group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either display_id or group_id must be provided"
        )
    
    db_schedule = Schedule(**schedule_data.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("/", response_model=List[ScheduleResponse])
async def get_schedules(
    skip: int = 0,
    limit: int = 100,
    display_id: Optional[int] = None,
    group_id: Optional[int] = None,
    active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy harmonogramów (admin i operator)"""
    query = db.query(Schedule)
    
    if display_id:
        query = query.filter(Schedule.display_id == display_id)
    if group_id:
        query = query.filter(Schedule.group_id == group_id)
    if active is not None:
        query = query.filter(Schedule.active == active)
    
    schedules = query.order_by(Schedule.created_at.desc()).offset(skip).limit(limit).all()
    return schedules


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów harmonogramu"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja harmonogramu (tylko admin)"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    update_data = schedule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie harmonogramu (tylko admin)"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    db.delete(schedule)
    db.commit()
    return None


@router.get("/display/{display_id}/current", response_model=List[ScheduleForDisplay])
async def get_current_schedules_for_display(
    display_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie aktualnych harmonogramów dla wyświetlacza"""
    schedules = get_active_schedules_for_display(db, display_id)
    
    return [
        ScheduleForDisplay(
            id=s.id,
            content_id=s.content_id,
            start_time=s.start_time,
            end_time=s.end_time,
            display_duration_seconds=s.display_duration_seconds,
            priority=s.priority
        )
        for s in schedules
    ]


@router.get("/display/{display_id}/schedule", response_model=List[ScheduleForDisplay])
async def get_display_schedule(
    display_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobranie harmonogramu dla wyświetlacza (publiczny endpoint dla klienta)
    Zwraca wszystkie aktywne harmonogramy, nie tylko aktualne
    """
    from app.models.schedule import Schedule
    
    schedules = db.query(Schedule).filter(
        Schedule.display_id == display_id,
        Schedule.active == True
    ).order_by(Schedule.priority.desc(), Schedule.start_time).all()
    
    return [
        ScheduleForDisplay(
            id=s.id,
            content_id=s.content_id,
            start_time=s.start_time,
            end_time=s.end_time,
            display_duration_seconds=s.display_duration_seconds,
            priority=s.priority
        )
        for s in schedules
    ]

