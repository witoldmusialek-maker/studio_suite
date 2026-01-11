"""
Endpointy API dla alertów
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.alert import (
    AlertResponse,
    AlertUpdate,
    DisplayStatusHistoryResponse
)
from app.services.alert_service import resolve_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    display_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy alertów (admin i operator)"""
    query = db.query(Alert)
    
    if display_id:
        query = query.filter(Alert.display_id == display_id)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return alerts


@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie aktywnych (nierozwiązanych) alertów"""
    alerts = db.query(Alert).filter(
        Alert.resolved == False
    ).order_by(
        Alert.severity.desc(),
        Alert.created_at.desc()
    ).all()
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów alertu"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return alert


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert_endpoint(
    alert_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Oznaczenie alertu jako rozwiązany (tylko admin)"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    resolved_alert = resolve_alert(db, alert_id, resolved_by=current_user.id)
    return resolved_alert


@router.get("/display/{display_id}/history", response_model=List[DisplayStatusHistoryResponse])
async def get_display_status_history(
    display_id: int,
    limit: int = Query(default=100, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie historii statusów wyświetlacza"""
    from app.models.display_status_history import DisplayStatusHistory
    
    history = db.query(DisplayStatusHistory).filter(
        DisplayStatusHistory.display_id == display_id
    ).order_by(
        DisplayStatusHistory.created_at.desc()
    ).limit(limit).all()
    
    return history



