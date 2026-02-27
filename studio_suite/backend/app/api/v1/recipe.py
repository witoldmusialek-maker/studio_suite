"""Service recipe API and generated inventory issues."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff_member, get_current_user, require_salon_access
from app.database import get_db
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    InventoryIssue,
    InventoryIssueLine,
    LegacyProductCatalogItem,
    ServiceCatalogItem,
    ServiceRecipeItem,
    StaffMember,
    StockLocation,
)
from app.models.user import User, UserRole
from app.schemas.inventory import (
    ServiceRecipeItemCreate,
    ServiceRecipeItemRead,
    ServiceRecipeItemUpdate,
)

router = APIRouter(tags=["recipe"])


class GeneratedIssueResponse(BaseModel):
    issue_ids: list[int]


def _ensure_manager_or_admin(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/manager can modify recipe")


def _ensure_issue_generation_access(
    db: Session,
    current_user: User,
    current_staff: StaffMember | None,
    appointment: Appointment,
) -> None:
    require_salon_access(db, current_user, appointment.salon_id)
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.RECEPTIONIST}:
        return
    if current_user.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if current_staff is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile linked to user")


def _estimate_unit_cost(product: LegacyProductCatalogItem | None) -> Decimal:
    if product is None:
        return Decimal("0")
    for candidate in (product.purchase_price, product.purchase_price_c, product.catalog_net_price):
        if candidate is not None:
            return Decimal(str(candidate))
    return Decimal("0")


def _recipe_to_read(item: ServiceRecipeItem, product: LegacyProductCatalogItem | None) -> ServiceRecipeItemRead:
    return ServiceRecipeItemRead(
        id=item.id,
        service_id=item.service_id,
        product_family=item.product_family,
        product_id=item.product_id,
        product_name=product.name if product else None,
        planned_quantity=float(item.planned_quantity),
        unit=item.unit,
        note=item.note,
    )


@router.get("/services/{service_id}/recipe", response_model=list[ServiceRecipeItemRead])
async def list_service_recipe(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    if not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    items = db.query(ServiceRecipeItem).filter(ServiceRecipeItem.service_id == service_id).order_by(ServiceRecipeItem.id.asc()).all()
    product_ids = [item.product_id for item in items if item.product_id is not None]
    products_by_id = {}
    if product_ids:
        products_by_id = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
        }
    return [_recipe_to_read(item, products_by_id.get(item.product_id)) for item in items]


@router.post("/services/{service_id}/recipe", response_model=ServiceRecipeItemRead, status_code=status.HTTP_201_CREATED)
async def create_service_recipe_item(
    service_id: int,
    payload: ServiceRecipeItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_manager_or_admin(current_user)
    if not db.query(ServiceCatalogItem.id).filter(ServiceCatalogItem.id == service_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    product = None
    if payload.product_id is not None:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == payload.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    item = ServiceRecipeItem(
        service_id=service_id,
        product_family=(payload.product_family or "").strip() or None,
        product_id=payload.product_id,
        planned_quantity=Decimal(str(payload.planned_quantity)),
        unit=payload.unit.strip().upper(),
        note=(payload.note or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _recipe_to_read(item, product)


@router.patch("/services/{service_id}/recipe/{recipe_id}", response_model=ServiceRecipeItemRead)
async def update_service_recipe_item(
    service_id: int,
    recipe_id: int,
    payload: ServiceRecipeItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_manager_or_admin(current_user)
    item = (
        db.query(ServiceRecipeItem)
        .filter(ServiceRecipeItem.id == recipe_id, ServiceRecipeItem.service_id == service_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")
    product = None
    provided = payload.model_fields_set
    if "product_id" in provided:
        if payload.product_id is not None:
            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == payload.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        item.product_id = payload.product_id
    elif item.product_id is not None:
        product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == item.product_id).first()
    if "product_family" in provided:
        item.product_family = (payload.product_family or "").strip() or None
    if "planned_quantity" in provided and payload.planned_quantity is not None:
        item.planned_quantity = Decimal(str(payload.planned_quantity))
    if "unit" in provided and payload.unit is not None:
        item.unit = payload.unit.strip().upper()
    if "note" in provided:
        item.note = (payload.note or "").strip() or None
    db.commit()
    db.refresh(item)
    return _recipe_to_read(item, product)


@router.delete("/services/{service_id}/recipe/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_recipe_item(
    service_id: int,
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_manager_or_admin(current_user)
    item = (
        db.query(ServiceRecipeItem)
        .filter(ServiceRecipeItem.id == recipe_id, ServiceRecipeItem.service_id == service_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe item not found")
    db.delete(item)
    db.commit()
    return None


@router.post("/appointments/{appointment_id}/generate-issues", response_model=GeneratedIssueResponse)
async def generate_inventory_issues_for_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    current_staff: StaffMember | None = Depends(get_current_staff_member),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if (appointment.status or "").lower() != "done":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Issues can be generated only for done appointments")

    _ensure_issue_generation_access(db, current_user, current_staff, appointment)

    stock_location = (
        db.query(StockLocation)
        .filter(
            StockLocation.salon_id == appointment.salon_id,
            StockLocation.is_active.is_(True),
            StockLocation.location_type.in_(["BACKBAR", "MIXED"]),
        )
        .order_by(StockLocation.location_type.asc(), StockLocation.code.asc())
        .first()
    )
    if not stock_location:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active BACKBAR/MIXED stock location in salon")

    performed_lines = (
        db.query(AppointmentPerformedLine)
        .filter(AppointmentPerformedLine.appointment_id == appointment_id)
        .order_by(AppointmentPerformedLine.id.asc())
        .all()
    )
    if not performed_lines:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment has no performed lines")

    service_ids = sorted({line.service_id for line in performed_lines})
    recipes_by_service: dict[int, list[ServiceRecipeItem]] = {}
    if service_ids:
        for item in (
            db.query(ServiceRecipeItem)
            .filter(ServiceRecipeItem.service_id.in_(service_ids))
            .order_by(ServiceRecipeItem.id.asc())
            .all()
        ):
            recipes_by_service.setdefault(item.service_id, []).append(item)

    product_ids = {item.product_id for rows in recipes_by_service.values() for item in rows if item.product_id is not None}
    products_by_id = {}
    if product_ids:
        products_by_id = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id.in_(product_ids)).all()
        }

    issue_ids: list[int] = []
    for performed_line in performed_lines:
        recipe_items = recipes_by_service.get(performed_line.service_id, [])
        if not recipe_items:
            continue

        existing_issue = (
            db.query(InventoryIssue)
            .filter(InventoryIssue.performed_line_id == performed_line.id)
            .order_by(InventoryIssue.id.asc())
            .first()
        )
        if existing_issue:
            issue_ids.append(existing_issue.id)
            continue

        issue = InventoryIssue(
            salon_id=appointment.salon_id,
            stock_location_id=stock_location.id,
            appointment_id=appointment.id,
            service_id=performed_line.service_id,
            performed_line_id=performed_line.id,
            staff_id=performed_line.worker_id,
            issue_time=performed_line.performed_at,
            status="PLANNED",
            remarks="Wygenerowano z receptury uslugi",
        )
        db.add(issue)
        db.flush()

        for recipe_item in recipe_items:
            product = products_by_id.get(recipe_item.product_id) if recipe_item.product_id is not None else None
            db.add(
                InventoryIssueLine(
                    inventory_issue_id=issue.id,
                    appointment_id=appointment.id,
                    service_id=performed_line.service_id,
                    recipe_item_id=recipe_item.id,
                    performed_line_id=performed_line.id,
                    product_id=recipe_item.product_id,
                    quantity_planned=recipe_item.planned_quantity,
                    quantity_actual=None,
                    unit=recipe_item.unit,
                    unit_cost=_estimate_unit_cost(product),
                    total_cost=Decimal("0"),
                )
            )

        issue_ids.append(issue.id)

    db.commit()
    return GeneratedIssueResponse(issue_ids=issue_ids)
