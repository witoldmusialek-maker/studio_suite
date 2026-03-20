"""
Dependencies dla endpointów API
"""
from __future__ import annotations

from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.salon_core import StaffMember, StaffSalonMembership
from app.models.user import User, UserRole, UserSession
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

SUPERADMIN_ALLOWED_PREFIXES = (
    "/api/v1/tenants",
    "/api/v1/auth/me",
    "/api/v1/auth/totp/",
    "/api/v1/auth/change-password",
)


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
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
    token_tenant_id = payload.get("tid")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if token_tenant_id is not None:
        try:
            if int(token_tenant_id) != int(user.tenant_id):
                raise credentials_exception
        except (TypeError, ValueError):
            raise credentials_exception

    session_key: str | None = payload.get("sid")
    if session_key:
        db.query(UserSession).filter(
            UserSession.session_key == session_key,
            UserSession.user_id == user.id,
            UserSession.tenant_id == user.tenant_id,
        ).update({"last_seen": datetime.utcnow()})
        db.commit()

    if bool(getattr(user, "is_superadmin", False)):
        request_path = request.url.path if request else ""
        if not any(request_path.startswith(prefix) for prefix in SUPERADMIN_ALLOWED_PREFIXES):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superadmin has access only to tenant management endpoints",
            )
    
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


def get_current_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not bool(getattr(current_user, "is_superadmin", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin permissions required",
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
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN}:
        return
    staff_member = db.query(StaffMember).filter(StaffMember.user_id == current_user.id).first()
    allowed_salons = get_staff_allowed_salons(db, staff_member)
    if salon_id not in allowed_salons:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this salon")
