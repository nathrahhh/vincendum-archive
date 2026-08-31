"""Tests for portfolio position queries via Deal → Client relationships."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.models.position import PositionORM
from app.services.position_service import get_positions_for_portfolio

_TEST_TABLES = [
    LenderORM.__table__,
    PortfolioORM.__table__,
    ClientORM.__table__,
    DealORM.__table__,
    PositionORM.__table__,
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


def _seed_lender_and_portfolios(db: Session) -> None:
    db.add(
        LenderORM(
            id=1,
            name="Lender A",
            slug="lender-a",
            capital_base=10_000_000,
        )
    )
    db.add_all(
        [
            PortfolioORM(
                id=1,
                name="Main",
                lender_id=1,
                capital_allocation=5_000_000,
            ),
            PortfolioORM(
                id=2,
                name="Secondary",
                lender_id=1,
                capital_allocation=1_000_000,
            ),
        ]
    )
    db.flush()


def _add_approved_deal_with_position(
    db: Session,
    *,
    client_id: int,
    portfolio_id: int | None,
    deal_id: int,
    position_id: int,
    client_name: str,
    industry: str,
    deal_name: str,
    value: float,
) -> None:
    db.add(
        ClientORM(
            id=client_id,
            name=client_name,
            industry=industry,
            credit_limit=1_000_000,
            lender_id=1,
            portfolio_id=portfolio_id,
        )
    )
    db.add(
        DealORM(
            id=deal_id,
            client_id=client_id,
            name=deal_name,
            value=value,
            status="APPROVED",
        )
    )
    db.add(
        PositionORM(
            id=position_id,
            deal_id=deal_id,
            value=value,
        )
    )
    db.flush()


def test_get_positions_for_portfolio_returns_derived_details(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolios(db_session)
    _add_approved_deal_with_position(
        db_session,
        client_id=10,
        portfolio_id=1,
        deal_id=100,
        position_id=1,
        client_name="Tech Co",
        industry="Technology",
        deal_name="Tech Loan",
        value=500_000,
    )
    db_session.commit()

    positions = get_positions_for_portfolio(db_session, portfolio_id=1)

    assert len(positions) == 1
    assert positions[0] == {
        "position_id": 1,
        "value": 500_000.0,
        "deal_id": 100,
        "deal_name": "Tech Loan",
        "client_id": 10,
        "client_name": "Tech Co",
        "client_industry": "Technology",
    }


def test_get_positions_for_portfolio_excludes_other_portfolios(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolios(db_session)
    _add_approved_deal_with_position(
        db_session,
        client_id=10,
        portfolio_id=1,
        deal_id=100,
        position_id=1,
        client_name="Portfolio One Co",
        industry="Technology",
        deal_name="Loan A",
        value=100_000,
    )
    _add_approved_deal_with_position(
        db_session,
        client_id=20,
        portfolio_id=2,
        deal_id=200,
        position_id=2,
        client_name="Portfolio Two Co",
        industry="Retail",
        deal_name="Loan B",
        value=900_000,
    )
    db_session.commit()

    positions = get_positions_for_portfolio(db_session, portfolio_id=1)

    assert len(positions) == 1
    assert positions[0]["client_id"] == 10
    assert positions[0]["value"] == 100_000.0


def test_get_positions_for_portfolio_excludes_unassigned_clients(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolios(db_session)
    _add_approved_deal_with_position(
        db_session,
        client_id=10,
        portfolio_id=1,
        deal_id=100,
        position_id=1,
        client_name="Assigned Co",
        industry="Technology",
        deal_name="Assigned Loan",
        value=100_000,
    )
    _add_approved_deal_with_position(
        db_session,
        client_id=30,
        portfolio_id=None,
        deal_id=300,
        position_id=3,
        client_name="Unassigned Co",
        industry="Healthcare",
        deal_name="Orphan Loan",
        value=500_000,
    )
    db_session.commit()

    positions = get_positions_for_portfolio(db_session, portfolio_id=1)

    assert len(positions) == 1
    assert positions[0]["client_id"] == 10


def test_get_positions_for_portfolio_empty_when_no_positions(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolios(db_session)
    db_session.commit()

    assert get_positions_for_portfolio(db_session, portfolio_id=1) == []
