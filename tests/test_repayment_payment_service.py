"""Tests for recording payments against RepaymentORM rows."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.repayment import RepaymentORM
from app.services.repayment_payment_service import record_payment


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            ClientORM.__table__,
            DealORM.__table__,
            RepaymentORM.__table__,
        ],
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                RepaymentORM.__table__,
                DealORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed_deal(db: Session) -> None:
    db.add(LenderORM(id=1, name="Lender A", slug="lender-a"))
    db.add(
        ClientORM(
            id=2,
            name="Client Two",
            industry="tech",
            credit_limit=100_000.0,
            lender_id=1,
        )
    )
    db.add(
        DealORM(
            id=10,
            client_id=2,
            name="Term Loan",
            value=100_000.0,
            status="APPROVED",
        )
    )
    db.commit()


def _repayment(
    *,
    repayment_id: int = 1,
    interest_due: float = 100.0,
    principal_due: float = 900.0,
    total_due: float | None = None,
    interest_paid: float = 0.0,
    principal_paid: float = 0.0,
    total_paid: float = 0.0,
    status: str = "SCHEDULED",
    paid_at: date | None = None,
) -> RepaymentORM:
    due = total_due if total_due is not None else interest_due + principal_due
    return RepaymentORM(
        id=repayment_id,
        deal_id=10,
        due_date=date(2026, 2, 1),
        principal_due=principal_due,
        interest_due=interest_due,
        total_due=due,
        principal_paid=principal_paid,
        interest_paid=interest_paid,
        total_paid=total_paid,
        status=status,
        paid_at=paid_at,
    )


def _snapshot(row: RepaymentORM) -> tuple[float, float, float, str, date | None]:
    return (
        row.principal_paid,
        row.interest_paid,
        row.total_paid,
        row.status,
        row.paid_at,
    )


def test_successful_full_payment(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    paid_on = date(2026, 2, 5)
    row = record_payment(db_session, 1, 1_000.0, paid_at=paid_on)

    assert row.interest_paid == 100.0
    assert row.principal_paid == 900.0
    assert row.total_paid == 1_000.0
    assert row.status == "PAID"
    assert row.paid_at == paid_on


def test_partial_payment_covers_interest_then_principal(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    row = record_payment(db_session, 1, 300.0)

    assert row.interest_paid == 100.0
    assert row.principal_paid == 200.0
    assert row.total_paid == 300.0
    assert row.status == "PARTIALLY_PAID"
    assert row.paid_at is None


def test_payment_smaller_than_interest(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    row = record_payment(db_session, 1, 50.0)

    assert row.interest_paid == 50.0
    assert row.principal_paid == 0.0
    assert row.total_paid == 50.0
    assert row.status == "PARTIALLY_PAID"
    assert row.paid_at is None


def test_payment_exactly_equal_to_remaining_balance(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(
        _repayment(
            interest_paid=100.0,
            principal_paid=200.0,
            total_paid=300.0,
            status="PARTIALLY_PAID",
        )
    )
    db_session.commit()

    row = record_payment(db_session, 1, 700.0, paid_at=date(2026, 3, 1))

    assert row.interest_paid == 100.0
    assert row.principal_paid == 900.0
    assert row.total_paid == 1_000.0
    assert row.status == "PAID"
    assert row.paid_at == date(2026, 3, 1)


def test_payment_greater_than_outstanding_returns_400(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    before = _snapshot(db_session.get(RepaymentORM, 1))  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        record_payment(db_session, 1, 1_000.01)

    assert exc_info.value.status_code == 400
    db_session.rollback()
    after = _snapshot(db_session.get(RepaymentORM, 1))  # type: ignore[arg-type]
    assert after == before


def test_zero_payment_returns_400(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        record_payment(db_session, 1, 0.0)

    assert exc_info.value.status_code == 400


def test_negative_payment_returns_400(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        record_payment(db_session, 1, -10.0)

    assert exc_info.value.status_code == 400


def test_payment_against_already_paid_returns_400(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(
        _repayment(
            interest_paid=100.0,
            principal_paid=900.0,
            total_paid=1_000.0,
            status="PAID",
            paid_at=date(2026, 2, 5),
        )
    )
    db_session.commit()

    before = _snapshot(db_session.get(RepaymentORM, 1))  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        record_payment(db_session, 1, 50.0)

    assert exc_info.value.status_code == 400
    db_session.rollback()
    after = _snapshot(db_session.get(RepaymentORM, 1))  # type: ignore[arg-type]
    assert after == before


def test_nonexistent_repayment_returns_404(db_session: Session) -> None:
    _seed_deal(db_session)

    with pytest.raises(HTTPException) as exc_info:
        record_payment(db_session, 999, 100.0)

    assert exc_info.value.status_code == 404


def test_payment_is_persisted(db_session: Session) -> None:
    _seed_deal(db_session)
    db_session.add(_repayment())
    db_session.commit()

    record_payment(db_session, 1, 300.0)

    row = db_session.execute(
        select(RepaymentORM).where(RepaymentORM.id == 1)
    ).scalar_one()
    assert row.interest_paid == 100.0
    assert row.principal_paid == 200.0
    assert row.total_paid == 300.0
    assert row.status == "PARTIALLY_PAID"
