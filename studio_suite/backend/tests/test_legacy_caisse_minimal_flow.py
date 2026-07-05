from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Tenant, User
from app.models.salon_core import (
    Payment,
    PaymentAllocation,
    PaymentLine,
    Sale,
    SaleLine,
    Salon,
    ServiceCatalogItem,
    StaffMember,
    StaffSalonMembership,
)
from app.models.user import UserRole
from app.api.v1.legacy_caisse import create_fiche, list_fiches
from app.schemas.legacy_caisse import LegacyCaisseFicheCreate, LegacyCaisseLineWrite


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Tenant.__table__,
        User.__table__,
        Salon.__table__,
        StaffMember.__table__,
        StaffSalonMembership.__table__,
        ServiceCatalogItem.__table__,
        Sale.__table__,
        SaleLine.__table__,
        Payment.__table__,
        PaymentAllocation.__table__,
        PaymentLine.__table__,
    ]
    saved_indexes = {table: set(table.indexes) for table in tables}
    for table in tables:
        table.indexes.clear()
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine, tables=list(reversed(tables)))
        for table, indexes in saved_indexes.items():
            table.indexes.update(indexes)


def seed_minimal_caisse_data(db):
    tenant = Tenant(id=1, code="T1", name="Tenant 1", is_active=True)
    user = User(
        id=1,
        tenant_id=1,
        username="manager",
        password_hash="x",
        role=UserRole.MANAGER_MAIN,
        legacy_caisse_enabled=True,
    )
    salon_a = Salon(id=10, tenant_id=1, code="A", name="Salon A")
    salon_b = Salon(id=20, tenant_id=1, code="B", name="Salon B")
    staff_a = StaffMember(id=100, tenant_id=1, salon_id=10, legacy_code="01", display_name="Ada")
    staff_b = StaffMember(id=200, tenant_id=1, salon_id=20, legacy_code="02", display_name="Ben")
    service = ServiceCatalogItem(id=300, legacy_code="0001", name="Cut", default_price=100)
    db.add_all([tenant, user, salon_a, salon_b, staff_a, staff_b, service])
    db.commit()
    return user, salon_a, salon_b, staff_a, staff_b, service


def make_payload(*, salon_id: int, staff_id: int, service_id: int = 300) -> LegacyCaisseFicheCreate:
    return LegacyCaisseFicheCreate(
        salon_id=salon_id,
        sale_time=datetime(2026, 7, 5, 12, 0, 0),
        payment_method="cash",
        lines=[
            LegacyCaisseLineWrite(
                line_kind="service",
                staff_id=staff_id,
                service_id=service_id,
                legacy_worker_code="01",
                legacy_service_code="0001",
                label="Cut",
                quantity=1,
                unit_price=100,
            )
        ],
    )


def test_create_fiche_persists_sale_payment_and_current_month_list(db_session):
    user, salon_a, _salon_b, staff_a, _staff_b, service = seed_minimal_caisse_data(db_session)

    created = asyncio.run(create_fiche(make_payload(salon_id=salon_a.id, staff_id=staff_a.id, service_id=service.id), user, db_session))
    fiches = asyncio.run(list_fiches(salon_id=salon_a.id, month="2026-07", current_user=user, db=db_session))

    assert created.sale_id is not None
    assert created.total_gross == 100.0
    assert created.payment_method == "cash"
    assert created.lines[0].legacy_worker_code == "01"
    assert created.lines[0].legacy_service_code == "0001"
    assert len(fiches) == 1
    assert fiches[0].sale_id == created.sale_id
    assert db_session.query(Sale).count() == 1
    assert db_session.query(SaleLine).count() == 1


def test_create_fiche_rejects_staff_from_another_salon(db_session):
    user, salon_a, _salon_b, _staff_a, staff_b, service = seed_minimal_caisse_data(db_session)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(create_fiche(make_payload(salon_id=salon_a.id, staff_id=staff_b.id, service_id=service.id), user, db_session))

    assert exc.value.status_code in {403, 409}
    assert "salon" in str(exc.value.detail).lower()
    assert db_session.query(Sale).count() == 0


def test_create_fiche_rejects_service_not_available_in_salon(db_session):
    user, salon_a, _salon_b, staff_a, _staff_b, service = seed_minimal_caisse_data(db_session)
    service.is_active = False
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(create_fiche(make_payload(salon_id=salon_a.id, staff_id=staff_a.id, service_id=service.id), user, db_session))

    assert exc.value.status_code in {404, 409}
    assert "service" in str(exc.value.detail).lower()
    assert db_session.query(Sale).count() == 0
