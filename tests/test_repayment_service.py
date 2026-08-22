"""Tests for repayment schedule persistence (repayment_service)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.repayment import RepaymentORM
from app.services.repayment_service import generate_and_store_schedule


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


def _seed_lender_and_client(db: Session) -> None:
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
    db.commit()


def _valid_deal(**overrides: object) -> DealORM:
    values: dict[str, object] = {
        "id": 10,
        "client_id": 2,
        "name": "Term Loan",
        "value": 100_000.0,
        "status": "APPROVED",
        "principal_amount": 100_000.0,
        "interest_rate": 7.0,
        "interest_rate_type": "fixed",
        "repayment_method": "amortizing",
        "term_months": 12,
        "payment_frequency": "monthly",
        "first_payment_date": date(2026, 2, 1),
    }
    values.update(overrides)
    return DealORM(**values)  # type: ignore[arg-type]


def test_generate_and_store_schedule_success(db_session: Session) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(_valid_deal(term_months=12))
    db_session.commit()

    repayments = generate_and_store_schedule(db_session, deal_id=10)

    assert len(repayments) == 12
    for row in repayments:
        assert row.deal_id == 10
        assert row.principal_due + row.interest_due == pytest.approx(row.total_due)
        assert row.principal_paid == 0
        assert row.interest_paid == 0
        assert row.total_paid == 0
        assert row.status == "SCHEDULED"
        assert row.paid_at is None
        assert row.id is not None


def test_schedule_is_persisted_in_database(db_session: Session) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(_valid_deal(term_months=3))
    db_session.commit()

    generate_and_store_schedule(db_session, deal_id=10)

    count = db_session.execute(
        select(func.count()).select_from(RepaymentORM).where(
            RepaymentORM.deal_id == 10
        )
    ).scalar_one()
    assert count == 3

    rows = db_session.execute(
        select(RepaymentORM)
        .where(RepaymentORM.deal_id == 10)
        .order_by(RepaymentORM.due_date)
    ).scalars().all()
    assert [row.due_date for row in rows] == [
        date(2026, 2, 1),
        date(2026, 3, 1),
        date(2026, 4, 1),
    ]
    assert sum(row.principal_due for row in rows) == pytest.approx(100_000.0)


def test_missing_deal_returns_404(db_session: Session) -> None:
    _seed_lender_and_client(db_session)

    with pytest.raises(HTTPException) as exc_info:
        generate_and_store_schedule(db_session, deal_id=999)

    assert exc_info.value.status_code == 404
    assert "999" in exc_info.value.detail


@pytest.mark.parametrize(
    "missing_field",
    [
        "principal_amount",
        "interest_rate",
        "term_months",
        "first_payment_date",
    ],
)
def test_missing_repayment_terms_returns_400(
    db_session: Session,
    missing_field: str,
) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(_valid_deal(**{missing_field: None}))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        generate_and_store_schedule(db_session, deal_id=10)

    assert exc_info.value.status_code == 400
    assert missing_field in exc_info.value.detail


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("interest_rate_type", "floating"),
        ("repayment_method", "interest_only"),
        ("payment_frequency", "quarterly"),
    ],
)
def test_unsupported_configuration_returns_400(
    db_session: Session,
    field: str,
    value: str,
) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(_valid_deal(**{field: value}))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        generate_and_store_schedule(db_session, deal_id=10)

    assert exc_info.value.status_code == 400
    assert "not currently supported" in exc_info.value.detail


def test_duplicate_schedule_returns_409(db_session: Session) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(_valid_deal(term_months=6))
    db_session.commit()

    first = generate_and_store_schedule(db_session, deal_id=10)
    assert len(first) == 6

    with pytest.raises(HTTPException) as exc_info:
        generate_and_store_schedule(db_session, deal_id=10)

    assert exc_info.value.status_code == 409

    count = db_session.execute(
        select(func.count()).select_from(RepaymentORM).where(
            RepaymentORM.deal_id == 10
        )
    ).scalar_one()
    assert count == 6


def test_bullet_schedule_is_accepted_and_persisted(db_session: Session) -> None:
    _seed_lender_and_client(db_session)
    db_session.add(
        _valid_deal(
            repayment_method="bullet",
            term_months=12,
            principal_amount=100_000.0,
            interest_rate=7.0,
        )
    )
    db_session.commit()

    repayments = generate_and_store_schedule(db_session, deal_id=10)

    assert len(repayments) == 12
    assert all(row.principal_due == 0.0 for row in repayments[:-1])
    assert repayments[-1].principal_due == 100_000.0
    monthly_interest = round(100_000.0 * 0.07 / 12, 2)
    assert all(row.interest_due == monthly_interest for row in repayments)
    assert all(row.status == "SCHEDULED" for row in repayments)
