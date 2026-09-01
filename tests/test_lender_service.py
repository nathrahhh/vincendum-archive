"""Tests for lender capital-base business rules."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.services.lender_service import (
    get_lender_capital_base,
    get_lender_for_user,
    validate_lender_capital_base,
    validate_portfolio_capital_allocation,
)

_TEST_TABLES = [
    LenderORM.__table__,
    PortfolioORM.__table__,
]


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=_TEST_TABLES)
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
        Base.metadata.drop_all(bind=engine, tables=list(reversed(_TEST_TABLES)))


def _seed_lenders_with_portfolios(db: Session) -> None:
    db.add_all(
        [
            LenderORM(
                id=1,
                name="Lender A",
                slug="lender-a",
                capital_base=1_000_000,
            ),
            LenderORM(
                id=2,
                name="Lender B",
                slug="lender-b",
                capital_base=5_000_000,
            ),
        ]
    )
    db.add_all(
        [
            PortfolioORM(
                id=1,
                name="Portfolio A",
                lender_id=1,
                capital_allocation=400_000,
            ),
            PortfolioORM(
                id=2,
                name="Portfolio B",
                lender_id=1,
                capital_allocation=300_000,
            ),
            PortfolioORM(
                id=3,
                name="Other Lender Portfolio",
                lender_id=2,
                capital_allocation=2_000_000,
            ),
        ]
    )
    db.commit()


def test_get_lender_capital_base(db_session: Session) -> None:
    _seed_lenders_with_portfolios(db_session)

    assert get_lender_capital_base(db_session, lender_id=1) == 1_000_000


def test_get_lender_for_user_missing_lender_raises(db_session: Session) -> None:
    with pytest.raises(ValueError, match="Lender 999 not found"):
        get_lender_for_user(db_session, lender_id=999)


def test_validate_portfolio_allocation_within_remaining_capital(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    validate_portfolio_capital_allocation(
        db_session,
        lender_id=1,
        proposed_allocation=200_000,
    )


def test_validate_portfolio_allocation_exactly_equal_to_remaining_capital(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    validate_portfolio_capital_allocation(
        db_session,
        lender_id=1,
        proposed_allocation=300_000,
    )


def test_validate_portfolio_allocation_exceeds_remaining_capital(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_portfolio_capital_allocation(
            db_session,
            lender_id=1,
            proposed_allocation=350_000,
        )

    assert exc_info.value.status_code == 400
    assert "would exceed lender capital base" in exc_info.value.detail


def test_validate_portfolio_allocation_ignores_other_lender_portfolios(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    validate_portfolio_capital_allocation(
        db_session,
        lender_id=1,
        proposed_allocation=300_000,
    )


def test_validate_portfolio_allocation_update_excluding_current_allocation(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    validate_portfolio_capital_allocation(
        db_session,
        lender_id=1,
        proposed_allocation=500_000,
        exclude_portfolio_id=1,
    )


def test_validate_portfolio_allocation_update_exceeds_capital_base(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_portfolio_capital_allocation(
            db_session,
            lender_id=1,
            proposed_allocation=800_000,
            exclude_portfolio_id=1,
        )

    assert exc_info.value.status_code == 400


def test_validate_portfolio_allocation_rejects_negative_allocation(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_portfolio_capital_allocation(
            db_session,
            lender_id=1,
            proposed_allocation=-1,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Capital allocation cannot be negative"


def test_validate_lender_capital_base_allows_lower_value_when_allocations_fit(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    validate_lender_capital_base(
        db_session,
        lender_id=1,
        proposed_capital_base=800_000,
    )


def test_validate_lender_capital_base_rejects_value_below_allocations(
    db_session: Session,
) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_lender_capital_base(
            db_session,
            lender_id=1,
            proposed_capital_base=600_000,
        )

    assert exc_info.value.status_code == 400
    assert "cannot be lower than total portfolio allocations" in exc_info.value.detail


def test_validate_lender_capital_base_rejects_zero(db_session: Session) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_lender_capital_base(
            db_session,
            lender_id=1,
            proposed_capital_base=0,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Capital base must be greater than zero"


def test_validate_lender_capital_base_rejects_negative(db_session: Session) -> None:
    _seed_lenders_with_portfolios(db_session)

    with pytest.raises(HTTPException) as exc_info:
        validate_lender_capital_base(
            db_session,
            lender_id=1,
            proposed_capital_base=-100,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Capital base must be greater than zero"


def test_validate_lender_capital_base_missing_lender_raises(
    db_session: Session,
) -> None:
    with pytest.raises(ValueError, match="Lender 999 not found"):
        validate_lender_capital_base(
            db_session,
            lender_id=999,
            proposed_capital_base=1_000_000,
        )
