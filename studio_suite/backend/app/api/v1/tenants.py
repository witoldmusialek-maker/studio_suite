import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_superadmin
from app.database import get_db
from app.models.user import Tenant, TenantModuleLicense, User, UserRole
from app.schemas.user import (
    TenantCreate,
    TenantModuleLicensePayload,
    TenantModuleLicenseResponse,
    TenantResponse,
    TenantUpdate,
)
from app.utils.security import get_password_hash

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _normalize_code(value: str) -> str:
    return value.strip().upper().replace(" ", "_")


def _normalize_username(value: str) -> str:
    return value.strip().lower()


def _validate_password_strength(password: str) -> None:
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


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    return db.query(Tenant).order_by(Tenant.id.asc()).all()


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    code = _normalize_code(payload.code)
    if db.query(Tenant).filter(Tenant.code == code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant code already exists")
    tenant = Tenant(
        code=code,
        name=payload.name.strip(),
        is_active=bool(payload.is_active),
        billing_plan=payload.billing_plan.strip().upper(),
        billing_cycle=payload.billing_cycle.strip().lower(),
        monthly_base_price=payload.monthly_base_price,
        billing_email=(payload.billing_email or "").strip() or None,
    )
    db.add(tenant)
    db.flush()
    if payload.admin_username:
        admin_username = _normalize_username(payload.admin_username)
        if db.query(User).filter(User.username == admin_username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin username already exists")
        if not payload.admin_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin password is required")
        _validate_password_strength(payload.admin_password)
        db.add(
            User(
                tenant_id=tenant.id,
                username=admin_username,
                password_hash=get_password_hash(payload.admin_password),
                role=UserRole.ADMIN,
                is_superadmin=False,
            )
        )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if payload.code is not None:
        code = _normalize_code(payload.code)
        existing = db.query(Tenant).filter(Tenant.code == code, Tenant.id != tenant_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant code already exists")
        tenant.code = code
    if payload.name is not None:
        tenant.name = payload.name.strip()
    if payload.is_active is not None:
        tenant.is_active = bool(payload.is_active)
    if payload.billing_plan is not None:
        tenant.billing_plan = payload.billing_plan.strip().upper()
    if payload.billing_cycle is not None:
        tenant.billing_cycle = payload.billing_cycle.strip().lower()
    if payload.monthly_base_price is not None:
        tenant.monthly_base_price = payload.monthly_base_price
    if payload.billing_email is not None:
        tenant.billing_email = payload.billing_email.strip() or None

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if tenant.id == 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default tenant cannot be deleted")
    try:
        db.delete(tenant)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant has linked data. Deactivate it instead.",
        ) from None
    return None


@router.get("/{tenant_id}/licenses", response_model=list[TenantModuleLicenseResponse])
async def list_tenant_licenses(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return (
        db.query(TenantModuleLicense)
        .filter(TenantModuleLicense.tenant_id == tenant_id)
        .order_by(TenantModuleLicense.module_code.asc())
        .all()
    )


@router.put("/{tenant_id}/licenses", response_model=list[TenantModuleLicenseResponse])
async def replace_tenant_licenses(
    tenant_id: int,
    payload: list[TenantModuleLicensePayload],
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    db.query(TenantModuleLicense).filter(TenantModuleLicense.tenant_id == tenant_id).delete()
    rows: list[TenantModuleLicense] = []
    for item in payload:
        rows.append(
            TenantModuleLicense(
                tenant_id=tenant_id,
                module_code=item.module_code.strip().upper(),
                is_enabled=bool(item.is_enabled),
                monthly_price=item.monthly_price,
                notes=(item.notes or "").strip() or None,
            )
        )
    if rows:
        db.add_all(rows)
    db.commit()
    return (
        db.query(TenantModuleLicense)
        .filter(TenantModuleLicense.tenant_id == tenant_id)
        .order_by(TenantModuleLicense.module_code.asc())
        .all()
    )
