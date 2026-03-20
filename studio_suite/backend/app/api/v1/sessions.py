from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, get_staff_allowed_salons
from app.database import get_db
from app.models.salon_core import Salon
from app.models.user import User, UserRole, UserSession
from app.schemas.user import SessionResponse

router = APIRouter(tags=["sessions"])

ACTIVE_SESSION_WINDOW_MINUTES = 15


@router.get("/sessions", response_model=list[SessionResponse])
async def list_active_sessions(
    salon_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    threshold = datetime.utcnow() - timedelta(minutes=ACTIVE_SESSION_WINDOW_MINUTES)
    query = db.query(UserSession, User, Salon).join(User, User.id == UserSession.user_id).outerjoin(Salon, Salon.id == UserSession.salon_id)
    query = query.filter(UserSession.last_seen >= threshold)

    if current_user.role in {UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        staff_member = get_current_staff_member(current_user=current_user, db=db)
        allowed_salons = get_staff_allowed_salons(db, staff_member)
        if salon_id is not None:
            if salon_id not in allowed_salons:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this salon")
            query = query.filter(UserSession.salon_id == salon_id)
        elif allowed_salons:
            query = query.filter(UserSession.salon_id.in_(sorted(allowed_salons)))
        else:
            query = query.filter(False)
        query = query.filter(UserSession.user_role == UserRole.RECEPTIONIST.value)
    elif salon_id is not None:
        query = query.filter(UserSession.salon_id == salon_id)

    rows = query.order_by(UserSession.last_seen.desc()).all()
    now = datetime.utcnow()
    return [
        SessionResponse(
            id=session.id,
            user_id=user.id,
            username=user.username,
            role=session.user_role,
            salon_id=session.salon_id,
            salon_name=salon.name if salon else None,
            online_since=session.created_at,
            last_seen=session.last_seen,
            online_seconds=max(0, int((now - (session.created_at or now)).total_seconds())),
            ip_address=session.ip_address,
            is_active=True,
        )
        for session, user, salon in rows
    ]


@router.get("/sessions/history", response_model=list[SessionResponse])
async def list_session_history(
    salon_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    threshold = datetime.utcnow() - timedelta(minutes=ACTIVE_SESSION_WINDOW_MINUTES)
    query = (
        db.query(UserSession, User, Salon)
        .join(User, User.id == UserSession.user_id)
        .outerjoin(Salon, Salon.id == UserSession.salon_id)
    )
    if salon_id is not None:
        query = query.filter(UserSession.salon_id == salon_id)

    rows = query.order_by(UserSession.created_at.desc(), UserSession.id.desc()).limit(limit).all()
    now = datetime.utcnow()
    return [
        SessionResponse(
            id=session.id,
            user_id=user.id,
            username=user.username,
            role=session.user_role,
            salon_id=session.salon_id,
            salon_name=salon.name if salon else None,
            online_since=session.created_at,
            last_seen=session.last_seen,
            online_seconds=max(0, int((now - (session.created_at or now)).total_seconds())),
            ip_address=session.ip_address,
            is_active=bool(session.last_seen and session.last_seen >= threshold),
        )
        for session, user, salon in rows
    ]
