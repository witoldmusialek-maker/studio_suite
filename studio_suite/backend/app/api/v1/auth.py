"""
Authentication endpoints.
"""
import asyncio
import random
import re
import secrets
import string
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
import pyotp
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_salon_access
from app.config import settings
from app.database import get_db
from app.models.salon_core import Salon, SmsGatewayDevice, SmsGatewayPairingCode, StaffMember
from app.models.user import Tenant, User, UserRole, UserSession
from app.schemas.token import Token
from app.schemas.user import (
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.notifications import send_sms_text
from app.utils.login_protection import LoginProtection
from app.utils.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

login_protection = LoginProtection(
    max_attempts=settings.LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.LOGIN_WINDOW_SECONDS,
    lockout_seconds=settings.LOGIN_LOCKOUT_SECONDS,
)

MANAGEABLE_ROLES = {
    "admin": {"admin", "manager", "manager_main", "manager_salon", "employee", "receptionist"},
    "manager": {"manager_salon", "employee", "receptionist"},
    "manager_main": {"manager_salon", "employee", "receptionist"},
    "manager_salon": {"employee", "receptionist"},
}


class SmsTestRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    message: str = Field(min_length=1, max_length=480)
    salon_id: int | None = Field(default=None, ge=1)


class SmsGatewayPairingCodeCreateRequest(BaseModel):
    salon_id: int = Field(ge=1)
    ttl_minutes: int = Field(default=10, ge=1, le=60)


class SmsGatewayPairingCodeRead(BaseModel):
    code: str
    salon_id: int
    expires_at: datetime


class SmsGatewayDeviceRead(BaseModel):
    id: int
    salon_id: int
    device_name: str
    device_uuid: str
    endpoint_url: str
    app_version: str | None = None
    is_active: bool
    last_seen_at: datetime | None = None
    created_at: datetime


class SmsGatewayRegisterRequest(BaseModel):
    pair_code: str = Field(min_length=4, max_length=32)
    device_name: str = Field(min_length=1, max_length=128)
    device_uuid: str = Field(min_length=6, max_length=128)
    endpoint_url: str = Field(min_length=12, max_length=512)
    app_version: str | None = Field(default=None, max_length=32)


class SmsGatewayRegisterResponse(BaseModel):
    device_id: int
    salon_id: int
    salon_name: str | None = None
    auth_token: str


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _validate_password_strength(password: str, username: str | None = None) -> None:
    issues: list[str] = []
    if len(password) < 10:
        issues.append("minimum length is 10 characters")
    if not re.search(r"[a-z]", password):
        issues.append("must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        issues.append("must contain an uppercase letter")
    if not re.search(r"\d", password):
        issues.append("must contain a digit")
    if any(ch.isspace() for ch in password):
        issues.append("cannot contain spaces")
    if issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements: " + "; ".join(issues),
        )


def _generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    seed = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.ascii_lowercase),
    ]
    while len(seed) < max(10, length):
        seed.append(secrets.choice(alphabet))
    secrets.SystemRandom().shuffle(seed)
    generated = "".join(seed)
    _validate_password_strength(generated)
    return generated


def _get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _can_manage(current_user: User, target_role: str) -> bool:
    return target_role in MANAGEABLE_ROLES.get(current_user.role.value, set())


def _require_manager_user(user: User) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _generate_pair_code(length: int = 8) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _normalize_pair_code(value: str) -> str:
    return "".join(ch for ch in (value or "").strip().upper() if ch.isalnum())


def _validate_endpoint_url(endpoint_url: str) -> str:
    cleaned = (endpoint_url or "").strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url is required")
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url must start with http:// or https://")
    if not cleaned.endswith("/send"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url must end with /send")
    return cleaned


def _require_totp_user(user: User) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TOTP option is available only for admin/manager accounts",
        )


def _normalize_totp_code(code: str | None) -> str:
    if not code:
        return ""
    return "".join(ch for ch in code.strip() if ch.isdigit())


def _verify_totp_code(user: User, code: str | None) -> bool:
    normalized = _normalize_totp_code(code)
    if not user.totp_secret or not normalized:
        return False
    return bool(pyotp.TOTP(user.totp_secret).verify(normalized, valid_window=1))


def _to_user_response(db: Session, user: User) -> UserResponse:
    linked_staff = (
        db.query(StaffMember, Salon)
        .outerjoin(Salon, Salon.id == StaffMember.salon_id)
        .filter(StaffMember.user_id == user.id)
        .first()
    )
    linked_staff_id = None
    linked_staff_name = None
    linked_salon_id = None
    linked_salon_name = None
    if linked_staff:
        staff_row, salon_row = linked_staff
        linked_staff_id = staff_row.id
        linked_staff_name = f"{(staff_row.first_name or '').strip()} {(staff_row.last_name or '').strip()}".strip() or (staff_row.display_name or None)
        linked_salon_id = staff_row.salon_id
        linked_salon_name = salon_row.name if salon_row else None
    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
        linked_staff_id=linked_staff_id,
        linked_staff_name=linked_staff_name,
        linked_salon_id=linked_salon_id,
        linked_salon_name=linked_salon_name,
        is_superadmin=bool(user.is_superadmin),
        totp_enabled=bool(user.totp_enabled),
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    user_credentials: UserLogin,
    db: Session = Depends(get_db),
):
    username = _normalize_username(user_credentials.username)
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

    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        login_protection.register_failure(ip_key)
        login_protection.register_failure(user_key)
        await asyncio.sleep(random.uniform(0.25, 0.55))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.MANAGER_MAIN, UserRole.MANAGER_SALON} and user.totp_enabled:
        if not user_credentials.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP_REQUIRED",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not _verify_totp_code(user, user_credentials.totp_code):
            login_protection.register_failure(ip_key)
            login_protection.register_failure(user_key)
            await asyncio.sleep(random.uniform(0.25, 0.55))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP_INVALID",
                headers={"WWW-Authenticate": "Bearer"},
            )

    login_protection.reset(user_key)
    login_protection.reset(ip_key)

    user.last_login = datetime.utcnow()
    linked_staff = db.query(StaffMember).filter(StaffMember.user_id == user.id).first()
    session_key = uuid.uuid4().hex
    db.add(
        UserSession(
            tenant_id=user.tenant_id,
            user_id=user.id,
            salon_id=linked_staff.salon_id if linked_staff else None,
            session_key=session_key,
            user_role=user.role.value,
            ip_address=ip,
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )
    )
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "sid": session_key, "tid": user.tenant_id},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager", "manager_main", "manager_salon"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or manager can register users",
        )
    if not _can_manage(current_user, user_data.role.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for selected role",
        )

    username = _normalize_username(user_data.username)
    _validate_password_strength(user_data.password, username=username)

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    db_user = User(
        tenant_id=current_user.tenant_id,
        username=username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return _to_user_response(db, db_user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: str | None = Query(default=None),
    available: bool = Query(default=False),
    staff_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_filters: set[str] = set()
    if role:
        role_filters = {
            token.strip().lower()
            for token in re.split(r"[,\|]", role)
            if token.strip()
        }
        invalid_roles = role_filters - {member.value for member in UserRole}
        if invalid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported role filter: {', '.join(sorted(invalid_roles))}",
            )

    if current_user.role.value == "admin":
        users_query = db.query(User).filter(User.tenant_id == current_user.tenant_id)
        if role_filters:
            users_query = users_query.filter(User.role.in_([UserRole(value) for value in role_filters]))
        users = users_query.order_by(User.username.asc()).all()
        if available:
            assigned_user_ids = {
                row[0]
                for row in db.query(StaffMember.user_id)
                .filter(StaffMember.user_id.is_not(None))
                .filter(StaffMember.tenant_id == current_user.tenant_id)
                .filter((StaffMember.id != staff_id) if staff_id is not None else True)
                .all()
            }
            users = [user for user in users if user.id not in assigned_user_ids]
        return [_to_user_response(db, user) for user in users]
    if current_user.role.value in {"manager", "manager_salon"}:
        allowed_roles = {UserRole.EMPLOYEE, UserRole.RECEPTIONIST}
        if current_user.role.value == "manager":
            allowed_roles.add(UserRole.MANAGER_SALON)
    elif current_user.role.value == "manager_main":
        allowed_roles = {UserRole.MANAGER_SALON, UserRole.EMPLOYEE, UserRole.RECEPTIONIST}
    elif current_user.role.value == "admin":
        allowed_roles = set()
    else:
        allowed_roles = set()
    if current_user.role.value in {"manager", "manager_salon", "manager_main"}:
        if role_filters:
            requested_roles = {UserRole(value) for value in role_filters}
            allowed_roles &= requested_roles
        users_query = db.query(User).filter(
            User.tenant_id == current_user.tenant_id,
            User.role.in_(list(allowed_roles)),
        )
        users = users_query.order_by(User.username.asc()).all()
        if available:
            assigned_user_ids = {
                row[0]
                for row in db.query(StaffMember.user_id)
                .filter(StaffMember.user_id.is_not(None))
                .filter(StaffMember.tenant_id == current_user.tenant_id)
                .filter((StaffMember.id != staff_id) if staff_id is not None else True)
                .all()
            }
            users = [user for user in users if user.id not in assigned_user_ids]
        return [_to_user_response(db, user) for user in users]
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
    if current_user.role.value not in {"admin", "manager", "manager_main", "manager_salon"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not _can_manage(current_user, user.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if not _can_manage(current_user, payload.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions for selected role")
    if (
        current_user.id == user.id
        and current_user.role == UserRole.ADMIN
        and payload.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot remove own admin role",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return _to_user_response(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "manager", "manager_main", "manager_salon"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
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
    if current_user.role.value not in {"admin", "manager", "manager_main", "manager_salon"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not _can_manage(current_user, user.role.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if payload.new_password:
        _validate_password_strength(payload.new_password, username=user.username)
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
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    _validate_password_strength(payload.new_password, username=current_user.username)

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _to_user_response(db, current_user)


@router.post("/sms-test", status_code=status.HTTP_204_NO_CONTENT)
async def send_sms_test(
    payload: SmsTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_manager_user(current_user)
    if payload.salon_id is not None:
        require_salon_access(db, current_user, int(payload.salon_id))
    try:
        send_sms_text(payload.phone, payload.message.strip(), salon_id=payload.salon_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return None


@router.post("/sms-gateway/pairing-codes", response_model=SmsGatewayPairingCodeRead, status_code=status.HTTP_201_CREATED)
async def create_sms_gateway_pairing_code(
    payload: SmsGatewayPairingCodeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_manager_user(current_user)
    require_salon_access(db, current_user, payload.salon_id)

    salon = db.query(Salon).filter(Salon.id == payload.salon_id, Salon.tenant_id == current_user.tenant_id).first()
    if not salon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")

    expires_at = datetime.utcnow() + timedelta(minutes=payload.ttl_minutes)
    code = _generate_pair_code(8)
    while db.query(SmsGatewayPairingCode.id).filter(SmsGatewayPairingCode.pair_code == code).first():
        code = _generate_pair_code(8)

    row = SmsGatewayPairingCode(
        tenant_id=current_user.tenant_id,
        salon_id=payload.salon_id,
        pair_code=code,
        expires_at=expires_at,
        is_used=False,
        created_by_user_id=current_user.id,
    )
    db.add(row)
    db.commit()

    return SmsGatewayPairingCodeRead(code=code, salon_id=payload.salon_id, expires_at=expires_at)


@router.get("/sms-gateway/devices", response_model=list[SmsGatewayDeviceRead])
async def list_sms_gateway_devices(
    salon_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_manager_user(current_user)
    require_salon_access(db, current_user, salon_id)

    rows = (
        db.query(SmsGatewayDevice)
        .filter(
            SmsGatewayDevice.tenant_id == current_user.tenant_id,
            SmsGatewayDevice.salon_id == salon_id,
        )
        .order_by(SmsGatewayDevice.is_active.desc(), desc(SmsGatewayDevice.last_seen_at), desc(SmsGatewayDevice.created_at))
        .all()
    )
    return [
        SmsGatewayDeviceRead(
            id=row.id,
            salon_id=row.salon_id,
            device_name=row.device_name,
            device_uuid=row.device_uuid,
            endpoint_url=row.endpoint_url,
            app_version=row.app_version,
            is_active=bool(row.is_active),
            last_seen_at=row.last_seen_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.delete("/sms-gateway/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_sms_gateway_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_manager_user(current_user)
    row = (
        db.query(SmsGatewayDevice)
        .filter(SmsGatewayDevice.id == device_id, SmsGatewayDevice.tenant_id == current_user.tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    require_salon_access(db, current_user, row.salon_id)
    row.is_active = False
    db.commit()
    return None


@router.post("/sms-gateway/register", response_model=SmsGatewayRegisterResponse)
async def register_sms_gateway_device(
    payload: SmsGatewayRegisterRequest,
    db: Session = Depends(get_db),
):
    pair_code = _normalize_pair_code(payload.pair_code)
    if len(pair_code) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pairing code")

    pairing = (
        db.query(SmsGatewayPairingCode)
        .filter(
            SmsGatewayPairingCode.pair_code == pair_code,
            SmsGatewayPairingCode.is_used.is_(False),
            SmsGatewayPairingCode.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not pairing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pairing code invalid or expired")

    endpoint_url = _validate_endpoint_url(payload.endpoint_url)
    device_uuid = (payload.device_uuid or "").strip()
    if not device_uuid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="device_uuid is required")

    auth_token = secrets.token_hex(32)
    now = datetime.utcnow()
    row = (
        db.query(SmsGatewayDevice)
        .filter(
            SmsGatewayDevice.tenant_id == pairing.tenant_id,
            SmsGatewayDevice.salon_id == pairing.salon_id,
            SmsGatewayDevice.device_uuid == device_uuid,
        )
        .first()
    )
    if row:
        row.device_name = payload.device_name.strip()[:128]
        row.endpoint_url = endpoint_url
        row.auth_token = auth_token
        row.app_version = (payload.app_version or "").strip()[:32] or None
        row.is_active = True
        row.last_seen_at = now
    else:
        row = SmsGatewayDevice(
            tenant_id=pairing.tenant_id,
            salon_id=pairing.salon_id,
            device_uuid=device_uuid,
            device_name=payload.device_name.strip()[:128],
            endpoint_url=endpoint_url,
            auth_token=auth_token,
            app_version=(payload.app_version or "").strip()[:32] or None,
            is_active=True,
            last_seen_at=now,
            created_by_user_id=pairing.created_by_user_id,
        )
        db.add(row)

    pairing.is_used = True
    pairing.used_at = now
    db.commit()
    db.refresh(row)

    salon = db.query(Salon).filter(Salon.id == row.salon_id).first()
    return SmsGatewayRegisterResponse(
        device_id=row.id,
        salon_id=row.salon_id,
        salon_name=salon.name if salon else None,
        auth_token=auth_token,
    )


@router.get("/totp/status", response_model=TotpStatusResponse)
async def get_totp_status(current_user: User = Depends(get_current_user)):
    _require_totp_user(current_user)
    return TotpStatusResponse(enabled=bool(current_user.totp_enabled))


@router.post("/totp/setup", response_model=TotpSetupResponse)
async def setup_totp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_totp_user(current_user)
    secret = pyotp.random_base32()
    issuer = "Studio Suite"
    otpauth_uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username,
        issuer_name=issuer,
    )
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={quote(otpauth_uri)}"
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    db.commit()
    return TotpSetupResponse(secret=secret, otpauth_uri=otpauth_uri, qr_url=qr_url)


@router.post("/totp/enable", response_model=TotpStatusResponse)
async def enable_totp(
    payload: TotpVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_totp_user(current_user)
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP_NOT_SETUP")
    if not _verify_totp_code(current_user, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP_INVALID")
    current_user.totp_enabled = True
    db.commit()
    return TotpStatusResponse(enabled=True)


@router.post("/totp/disable", response_model=TotpStatusResponse)
async def disable_totp(
    payload: TotpVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_totp_user(current_user)
    if not current_user.totp_enabled:
        current_user.totp_secret = None
        db.commit()
        return TotpStatusResponse(enabled=False)
    if not _verify_totp_code(current_user, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP_INVALID")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    return TotpStatusResponse(enabled=False)
