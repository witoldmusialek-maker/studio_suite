"""
Dependencies dla endpointów API
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.salon_core import StaffMember, StaffSalonMembership
from app.models.user import User, UserRole
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Pobranie aktualnego użytkownika z tokena"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Pobranie aktualnego użytkownika admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_staff_member(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StaffMember | None:
    return db.query(StaffMember).filter(StaffMember.user_id == current_user.id).first()


def get_staff_allowed_salons(db: Session, staff_member: StaffMember | None) -> set[int]:
    if staff_member is None:
        return set()
    allowed: set[int] = set()
    if staff_member.salon_id:
        allowed.add(int(staff_member.salon_id))
    rows = (
        db.query(StaffSalonMembership.salon_id)
        .filter(
            StaffSalonMembership.staff_id == staff_member.id,
            StaffSalonMembership.is_active.is_(True),
        )
        .all()
    )
    allowed.update(int(row[0]) for row in rows)
    return allowed


def require_salon_access(db: Session, current_user: User, salon_id: int) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    staff_member = db.query(StaffMember).filter(StaffMember.user_id == current_user.id).first()
    allowed_salons = get_staff_allowed_salons(db, staff_member)
    if current_user.role == UserRole.MANAGER and not allowed_salons:
        return
    if salon_id not in allowed_salons:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this salon")
