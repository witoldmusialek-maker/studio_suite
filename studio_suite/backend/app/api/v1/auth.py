"""
Authentication endpoints.
"""
import asyncio
import random
import secrets
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.token import Token
from app.schemas.user import (
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.utils.login_protection import LoginProtection
from app.utils.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

login_protection = LoginProtection(
    max_attempts=settings.LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.LOGIN_WINDOW_SECONDS,
    lockout_seconds=settings.LOGIN_LOCKOUT_SECONDS,
)

MANAGEABLE_ROLES = {
    "admin": {"admin", "manager", "employee", "operator_displays", "operator_bells", "operator"},
    "manager": {"employee"},
}


def _generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _can_manage(current_user: User, target_role: str) -> bool:
    return target_role in MANAGEABLE_ROLES.get(current_user.role.value, set())


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    user_credentials: UserLogin,
    db: Session = Depends(get_db),
):
    username = user_credentials.username.strip().lower()
    ip = _get_client_ip(request)
    ip_key = f"ip:{ip}"
    user_key = f"user:{username}"

    blocked_seconds = max(
        login_protection.is_blocked(ip_key),
        login_protection.is_blocked(user_key),
    )
    if blocked_seconds > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Retry in {blocked_seconds}s.",
        )

    user = db.query(User).filter(User.username == user_credentials.username).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        login_protection.register_failure(ip_key)
        login_protection.register_failure(user_key)
        await asyncio.sleep(random.uniform(0.25, 0.55))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_protection.reset(user_key)
    login_protection.reset(ip_key)

    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or manager can register users",
        )
    if not _can_manage(current_user, user_data.role.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for selected role",
        )

    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    db_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value == "admin":
        return db.query(User).order_by(User.username.asc()).all()
    if current_user.role.value == "manager":
        return (
            db.query(User)
            .filter(User.role == UserRole.EMPLOYEE)
            .order_by(User.username.asc())
            .all()
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not _can_manage(current_user, user.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if not _can_manage(current_user, payload.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions for selected role")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    if not _can_manage(current_user, user.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    db.delete(user)
    db.commit()
    return None


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not _can_manage(current_user, user.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    plain_password = payload.new_password or _generate_temporary_password()
    user.password_hash = get_password_hash(plain_password)
    db.commit()

    return PasswordResetResponse(
        user_id=user.id,
        temporary_password=None if payload.new_password else plain_password,
        message="Password has been reset",
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_own_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is invalid")

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
