"""
CRUD endpoints for salons and staff resources.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.salon_core import Salon, StaffMember, StaffRole
from app.models.user import User
from app.schemas.resources import (
    SalonCreate,
    SalonRead,
    SalonUpdate,
    StaffCreate,
    StaffFunctionRead,
    StaffRead,
    StaffUpdate,
)

router = APIRouter(prefix="/resources", tags=["resources"])


def _ensure_admin_or_manager(current_user: User) -> None:
    if current_user.role.value not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


def _staff_to_read(staff: StaffMember, salons_by_id: dict[int, Salon], roles_by_id: dict[int, StaffRole]) -> StaffRead:
    salon = salons_by_id.get(staff.salon_id) if staff.salon_id else None
    role = roles_by_id.get(staff.role_id) if staff.role_id else None
    return StaffRead(
        id=staff.id,
        display_name=staff.display_name,
        salon_id=staff.salon_id,
        salon_name=salon.name if salon else None,
        role_id=staff.role_id,
        role_name=role.name if role else None,
        is_active=bool(staff.is_active),
        legacy_code=staff.legacy_code,
    )


@router.get("/salons", response_model=list[SalonRead])
async def list_salons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(Salon).order_by(Salon.name.asc()).all()


@router.post("/salons", response_model=SalonRead, status_code=status.HTTP_201_CREATED)
async def create_salon(
    payload: SalonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    code = payload.code.strip().upper()
    name = payload.name.strip()
    if db.query(Salon).filter(Salon.code == code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Salon code already exists")
    row = Salon(code=code, name=name, is_active=payload.is_active)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/salons/{salon_id}", response_model=SalonRead)
async def update_salon(
    salon_id: int,
    payload: SalonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(Salon).filter(Salon.id == salon_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.code is not None:
        code = payload.code.strip().upper()
        existing = db.query(Salon).filter(Salon.code == code, Salon.id != salon_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Salon code already exists")
        row.code = code
    if payload.name is not None:
        row.name = payload.name.strip()
    if payload.is_active is not None:
        row.is_active = payload.is_active
    db.commit()
    db.refresh(row)
    return row


@router.delete("/salons/{salon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_salon(
    salon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(Salon).filter(Salon.id == salon_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    db.query(StaffMember).filter(StaffMember.salon_id == salon_id).update({StaffMember.salon_id: None})
    db.delete(row)
    db.commit()
    return None


@router.get("/functions", response_model=list[StaffFunctionRead])
async def list_staff_functions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(StaffRole).order_by(StaffRole.name.asc()).all()


@router.get("/staff", response_model=list[StaffRead])
async def list_staff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    staff_rows = db.query(StaffMember).order_by(StaffMember.display_name.asc()).all()
    salons = db.query(Salon).all()
    roles = db.query(StaffRole).all()
    salons_by_id = {row.id: row for row in salons}
    roles_by_id = {row.id: row for row in roles}
    return [_staff_to_read(row, salons_by_id, roles_by_id) for row in staff_rows]


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    if payload.salon_id is not None and not db.query(Salon).filter(Salon.id == payload.salon_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if payload.role_id is not None and not db.query(StaffRole).filter(StaffRole.id == payload.role_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")

    row = StaffMember(
        display_name=payload.display_name.strip(),
        legacy_code=(payload.legacy_code or "").strip() or None,
        salon_id=payload.salon_id,
        role_id=payload.role_id,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    provided = payload.model_fields_set

    if "salon_id" in provided and payload.salon_id is not None and not db.query(Salon).filter(Salon.id == payload.salon_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")
    if "role_id" in provided and payload.role_id is not None and not db.query(StaffRole).filter(StaffRole.id == payload.role_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")

    if "display_name" in provided and payload.display_name is not None:
        row.display_name = payload.display_name.strip()
    if "legacy_code" in provided:
        row.legacy_code = payload.legacy_code.strip() or None
    if "salon_id" in provided:
        row.salon_id = payload.salon_id
    if "role_id" in provided:
        row.role_id = payload.role_id
    if "is_active" in provided and payload.is_active is not None:
        row.is_active = payload.is_active

    db.commit()
    db.refresh(row)
    salons_by_id = {item.id: item for item in db.query(Salon).all()}
    roles_by_id = {item.id: item for item in db.query(StaffRole).all()}
    return _staff_to_read(row, salons_by_id, roles_by_id)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin_or_manager(current_user)
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    db.delete(row)
    db.commit()
    return None
