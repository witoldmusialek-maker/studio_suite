"""
Endpointy autentykacji
"""
import secrets
import string
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserLogin,
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.schemas.token import Token
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.config import settings
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Logowanie użytkownika"""
    user = db.query(User).filter(User.username == user_credentials.username).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Aktualizacja last_login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    # Tworzenie tokena
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejestracja nowego użytkownika (tylko admin)."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can register users"
        )

    # Sprawdzenie czy użytkownik już istnieje
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Tworzenie użytkownika
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Lista użytkowników (tylko admin)."""
    return db.query(User).order_by(User.username.asc()).all()


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Aktualizacja roli użytkownika (tylko admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Usunięcie użytkownika (tylko admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()
    return None


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Reset hasła użytkownika (tylko admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    """Zmiana hasła zalogowanego użytkownika."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is invalid")

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Pobranie danych aktualnie zalogowanego użytkownika"""
    return current_user
