from __future__ import annotations

import asyncio
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.legacy_caisse import create_expense, create_fiche, get_daily_summary, upsert_cash_session
from app.database import Base
from app.models import Tenant, User
from app.models.salon_core import (
    CashierCashSession,
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
    LegacyCaisseExpenseWrite,
    LegacyCaisseFicheCreate,
    LegacyCaisseLineWrite,
    LegacyCaissePaymentAllocationWrite,
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
    user = User(
        id=1,
        tenant_id=1,
        username="manager",
        password_hash="x",
        role=UserRole.MANAGER_MAIN,
        legacy_caisse_enabled=True,
    )
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
            LegacyCaissePaymentAllocationWrite(method="card", amount=20),
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
                discount_amount=10,
            )
        ],
    )


def test_cash_session_open_close_and_closed_session_protection(db_session):
    user, salon, _staff, _service = seed_data(db_session)
    business_date = date(2026, 7, 5)

    opened = asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(salon_id=salon.id, business_date=business_date, opening_cash=100, status="OPEN"),
            user,
            db_session,
        )
    )
    duplicate = asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(salon_id=salon.id, business_date=business_date, opening_cash=100, status="OPEN"),
            user,
            db_session,
        )
    )
    closed = asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(
                salon_id=salon.id,
                business_date=business_date,
                opening_cash=100,
                closing_cash=150,
                status="CLOSED",
            ),
            user,
            db_session,
        )
    )

    assert opened.id == duplicate.id == closed.id
    assert db_session.query(CashierCashSession).count() == 1
    assert closed.status == "CLOSED"
    assert closed.closing_cash == 150.0

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            upsert_cash_session(
                LegacyCaisseCashSessionWrite(salon_id=salon.id, business_date=business_date, opening_cash=200, status="OPEN"),
                user,
                db_session,
            )
        )

    assert exc.value.status_code == 409
    assert "closed" in str(exc.value.detail).lower()


def test_daily_summary_calculates_cash_expected_and_difference(db_session):
    user, salon, staff, service = seed_data(db_session)
    business_date = date(2026, 7, 5)

    asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(salon_id=salon.id, business_date=business_date, opening_cash=100, status="OPEN"),
            user,
            db_session,
        )
    )
    asyncio.run(create_fiche(fiche_payload(salon_id=salon.id, staff_id=staff.id, service_id=service.id), user, db_session))
    asyncio.run(
        create_expense(
            LegacyCaisseExpenseWrite(
                salon_id=salon.id,
                expense_date=business_date,
                label="Coffee",
                amount_gross=15,
                vat_amount=0,
            ),
            user,
            db_session,
        )
    )
    asyncio.run(
        upsert_cash_session(
            LegacyCaisseCashSessionWrite(
                salon_id=salon.id,
                business_date=business_date,
                opening_cash=100,
                closing_cash=150,
                status="CLOSED",
            ),
            user,
            db_session,
        )
    )

    summary = asyncio.run(get_daily_summary(salon_id=salon.id, business_date=business_date, current_user=user, db=db_session))

    assert summary.opening_cash == 100.0
    assert summary.service_gross == 90.0
    assert summary.retail_gross == 0.0
    assert summary.discount_total == 10.0
    assert summary.payments_by_method == {"cash": 70.0, "card": 20.0}
    assert summary.cash_payments == 70.0
    assert summary.expenses_total == 15.0
    assert summary.expected_cash == 155.0
    assert summary.closing_cash == 150.0
    assert summary.cash_difference == -5.0
