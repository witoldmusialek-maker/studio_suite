from __future__ import annotations

import asyncio
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.legacy_caisse import create_fiche, get_daily_summary, get_fiche_audit, upsert_cash_session, void_fiche
from app.database import Base
from app.models import Tenant, User
from app.models.salon_core import (
    CashierCashSession,
    CashierCorrectionAudit,
    CashierExpense,
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
from app.schemas.legacy_caisse import (
    LegacyCaisseCashSessionWrite,
    LegacyCaisseFicheCreate,
    LegacyCaisseLineWrite,
    LegacyCaissePaymentAllocationWrite,
    LegacyCaisseVoidWrite,
)


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
        CashierCashSession.__table__,
        CashierExpense.__table__,
        CashierCorrectionAudit.__table__,
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


def seed_data(db):
    tenant = Tenant(id=1, code="T1", name="Tenant 1", is_active=True)
    user = User(id=1, tenant_id=1, username="manager", password_hash="x", role=UserRole.MANAGER_MAIN, legacy_caisse_enabled=True)
    salon = Salon(id=10, tenant_id=1, code="A", name="Salon A")
    staff = StaffMember(id=100, tenant_id=1, salon_id=10, legacy_code="01", display_name="Ada")
    service = ServiceCatalogItem(id=300, legacy_code="0001", name="Cut", default_price=100)
    db.add_all([tenant, user, salon, staff, service])
    db.commit()
    return user, salon, staff, service


def fiche_payload(*, salon_id: int, staff_id: int, service_id: int) -> LegacyCaisseFicheCreate:
    return LegacyCaisseFicheCreate(
        salon_id=salon_id,
        sale_time=datetime(2026, 7, 5, 12, 0, 0),
        payment_method="mixed",
        allocations=[
            LegacyCaissePaymentAllocationWrite(method="cash", amount=70),
            LegacyCaissePaymentAllocationWrite(method="card", amount=30),
        ],
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


def open_cash_day(user, salon, db_session, business_date=date(2026, 7, 5)):
    return asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(salon_id=salon.id, business_date=business_date, opening_cash=100, status="OPEN"),
            user,
            db_session,
        )
    )


def close_cash_day(user, salon, db_session, business_date=date(2026, 7, 5)):
    return asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(
                salon_id=salon.id,
                business_date=business_date,
                opening_cash=100,
                closing_cash=170,
                status="CLOSED",
            ),
            user,
            db_session,
        )
    )


def create_sample_fiche(user, salon, staff, service, db_session):
    return asyncio.run(create_fiche(fiche_payload(salon_id=salon.id, staff_id=staff.id, service_id=service.id), user, db_session))


def test_void_fiche_requires_reason_and_records_audit_history(db_session):
    user, salon, staff, service = seed_data(db_session)
    open_cash_day(user, salon, db_session)
    created = create_sample_fiche(user, salon, staff, service, db_session)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(void_fiche(created.sale_id, LegacyCaisseVoidWrite(reason="   "), user, db_session))
    assert exc.value.status_code == 422

    result = asyncio.run(void_fiche(created.sale_id, LegacyCaisseVoidWrite(reason="Client changed service"), user, db_session))
    history = asyncio.run(get_fiche_audit(created.sale_id, user, db_session))

    assert result.status == "VOID"
    assert result.reason == "Client changed service"
    assert len(history) == 1
    audit = history[0]
    assert audit.tenant_id == user.tenant_id
    assert audit.salon_id == salon.id
    assert audit.sale_id == created.sale_id
    assert audit.actor_user_id == user.id
    assert audit.action_type == "VOID"
    assert audit.reason == "Client changed service"
    assert audit.previous_status == "COMPLETED"
    assert audit.new_status == "VOID"


def test_closed_day_void_does_not_create_audit_success_record(db_session):
    user, salon, staff, service = seed_data(db_session)
    open_cash_day(user, salon, db_session)
    created = create_sample_fiche(user, salon, staff, service, db_session)
    close_cash_day(user, salon, db_session)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(void_fiche(created.sale_id, LegacyCaisseVoidWrite(reason="Late correction"), user, db_session))

    assert exc.value.status_code == 409
    assert db_session.query(CashierCorrectionAudit).count() == 0


def test_void_reason_keeps_daily_summary_exclusion_regression(db_session):
    user, salon, staff, service = seed_data(db_session)
    open_cash_day(user, salon, db_session)
    created = create_sample_fiche(user, salon, staff, service, db_session)

    asyncio.run(void_fiche(created.sale_id, LegacyCaisseVoidWrite(reason="Wrong service"), user, db_session))
    summary = asyncio.run(get_daily_summary(salon_id=salon.id, business_date=date(2026, 7, 5), current_user=user, db=db_session))

    assert summary.service_gross == 0.0
    assert summary.cash_payments == 0.0
    assert summary.expected_cash == 100.0
