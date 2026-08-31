"""Tests for lender industry exposure aggregation."""

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
from app.services.industry_exposure_service import get_industry_exposure

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


def _seed_lenders(db: Session) -> None:
    db.add_all(
        [
            LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000),
            LenderORM(id=2, name="Lender B", slug="lender-b", capital_base=10_000_000),
        ]
    )
    db.flush()


def _seed_portfolio(db: Session, *, portfolio_id: int, lender_id: int) -> None:
    db.add(
        PortfolioORM(
            id=portfolio_id,
            name=f"Portfolio {portfolio_id}",
            lender_id=lender_id,
            capital_allocation=5_000_000,
        )
    )
    db.flush()


def _add_position_for_client(
    db: Session,
    *,
    client_id: int,
    deal_id: int,
    position_id: int,
    lender_id: int,
    portfolio_id: int,
    industry: str,
    deal_name: str,
    value: float,
    client_name: str,
    assign_to_portfolio: bool = True,
) -> None:
    if db.get(ClientORM, client_id) is None:
        db.add(
            ClientORM(
                id=client_id,
                name=client_name,
                industry=industry,
                credit_limit=1_000_000,
                lender_id=lender_id,
                portfolio_id=portfolio_id if assign_to_portfolio else None,
            )
        )
    if db.get(PortfolioORM, portfolio_id) is None:
        _seed_portfolio(db, portfolio_id=portfolio_id, lender_id=lender_id)
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


def test_one_position_one_industry(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Tech Loan",
        value=500_000,
        client_name="Tech Co",
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert len(result) == 1
    assert result[0].industry == "Technology"
    assert result[0].value == 500_000
    assert result[0].percentage == 100.0


def test_multiple_positions_same_industry(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Tech Loan A",
        value=500_000,
        client_name="Tech Co",
    )
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=101,
        position_id=2,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Tech Loan B",
        value=300_000,
        client_name="Tech Co",
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert len(result) == 1
    assert result[0].industry == "Technology"
    assert result[0].value == 800_000
    assert result[0].percentage == 100.0


def test_multiple_industries_sorted_and_percentages(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Tech Loan A",
        value=500_000,
        client_name="Tech Co",
    )
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=101,
        position_id=2,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Tech Loan B",
        value=300_000,
        client_name="Tech Co",
    )
    _add_position_for_client(
        db_session,
        client_id=11,
        deal_id=102,
        position_id=3,
        lender_id=1,
        portfolio_id=1,
        industry="Manufacturing",
        deal_name="Factory Loan",
        value=200_000,
        client_name="Factory Co",
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert [item.industry for item in result] == ["Technology", "Manufacturing"]
    assert result[0].value == 800_000
    assert result[0].percentage == 80.0
    assert result[1].value == 200_000
    assert result[1].percentage == 20.0


def test_other_lender_positions_excluded(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _seed_portfolio(db_session, portfolio_id=2, lender_id=2)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="A Loan",
        value=100_000,
        client_name="Tech Co",
    )
    _add_position_for_client(
        db_session,
        client_id=20,
        deal_id=200,
        position_id=2,
        lender_id=2,
        portfolio_id=2,
        industry="Retail",
        deal_name="B Loan",
        value=900_000,
        client_name="Other Co",
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert len(result) == 1
    assert result[0].industry == "Technology"
    assert result[0].value == 100_000
    assert result[0].percentage == 100.0


def test_no_positions_returns_empty_list(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    db_session.commit()

    assert get_industry_exposure(db_session, lender_id=1) == []


def test_zero_total_exposure_percentages_are_zero(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Zero Loan",
        value=0.0,
        client_name="Zero Co",
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert len(result) == 1
    assert result[0].industry == "Technology"
    assert result[0].value == 0.0
    assert result[0].percentage == 0.0


def test_positions_without_portfolio_assignment_excluded(db_session: Session) -> None:
    _seed_lenders(db_session)
    _seed_portfolio(db_session, portfolio_id=1, lender_id=1)
    _add_position_for_client(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        lender_id=1,
        portfolio_id=1,
        industry="Technology",
        deal_name="Linked Loan",
        value=100_000,
        client_name="Tech Co",
    )
    _add_position_for_client(
        db_session,
        client_id=30,
        deal_id=300,
        position_id=3,
        lender_id=1,
        portfolio_id=1,
        industry="Healthcare",
        deal_name="Unassigned Loan",
        value=500_000,
        client_name="Unassigned Co",
        assign_to_portfolio=False,
    )
    db_session.commit()

    result = get_industry_exposure(db_session, lender_id=1)

    assert len(result) == 1
    assert result[0].value == 100_000
    assert result[0].percentage == 100.0
