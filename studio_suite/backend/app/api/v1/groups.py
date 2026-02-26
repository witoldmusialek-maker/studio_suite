"""
Endpointy API dla grup wyświetlaczy
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.group import Group
from app.models.display import Display
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupWithDisplays
)
from app.services.group_service import (
    get_displays_for_group,
    add_display_to_group,
    remove_display_from_group,
    validate_group_type
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Utworzenie grupy (tylko admin)"""
    # Walidacja typu grupy
    valid_types = ["horizontal", "vertical", "mixed", "single"]
    if group_data.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group type. Must be one of: {valid_types}"
        )
    
    db_group = Group(**group_data.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.get("/", response_model=List[GroupResponse])
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    floor_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy grup (admin i operator)"""
    query = db.query(Group)
    
    if floor_filter:
        query = query.filter(Group.floor == floor_filter)
    
    groups = query.order_by(Group.created_at.desc()).offset(skip).limit(limit).all()
    return groups


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegółów grupy"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group


@router.get("/{group_id}/displays", response_model=List[dict])
async def get_group_displays(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie wyświetlaczy w grupie"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    displays = get_displays_for_group(db, group_id)
    
    from app.schemas.display import DisplayResponse
    return [DisplayResponse.model_validate(d).model_dump() for d in displays]


@router.get("/{group_id}/with-displays", response_model=GroupWithDisplays)
async def get_group_with_displays(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie grupy z listą wyświetlaczy"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    displays = get_displays_for_group(db, group_id)
    from app.schemas.display import DisplayResponse
    
    group_dict = GroupResponse.model_validate(group).model_dump()
    group_dict["displays"] = [DisplayResponse.model_validate(d).model_dump() for d in displays]
    
    return group_dict


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja grupy (tylko admin)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    update_data = group_data.dict(exclude_unset=True)
    
    # Walidacja typu jeśli jest zmieniany
    if "type" in update_data:
        displays = get_displays_for_group(db, group_id)
        is_valid, error = validate_group_type(update_data["type"], len(displays))
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
    
    for field, value in update_data.items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie grupy (tylko admin)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Usunięcie przypisania wyświetlaczy do grupy
    displays = get_displays_for_group(db, group_id)
    for display in displays:
        display.group_id = None
    
    db.delete(group)
    db.commit()
    return None


@router.post("/{group_id}/displays/{display_id}", status_code=status.HTTP_200_OK)
async def add_display_to_group_endpoint(
    group_id: int,
    display_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Dodanie wyświetlacza do grupy (tylko admin)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    # Sprawdzenie czy wyświetlacz nie jest już w innej grupie
    if display.group_id and display.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display is already assigned to another group"
        )
    
    # Walidacja typu grupy
    current_displays = get_displays_for_group(db, group_id)
    is_valid, error = validate_group_type(group.type, len(current_displays) + 1)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    add_display_to_group(db, display_id, group_id)
    return {"message": "Display added to group"}


@router.delete("/{group_id}/displays/{display_id}", status_code=status.HTTP_200_OK)
async def remove_display_from_group_endpoint(
    group_id: int,
    display_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Usunięcie wyświetlacza z grupy (tylko admin)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    if display.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display is not in this group"
        )
    
    remove_display_from_group(db, display_id)
    return {"message": "Display removed from group"}

