"""Tests for portfolio monitoring aggregates."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.models.position import PositionORM
from app.services.portfolio_service import (
    create_portfolio,
    get_portfolio_for_lender,
    get_portfolios_for_lender,
    get_portfolio_industry_exposure,
    get_portfolio_summary,
)

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


def _seed_lender_and_portfolio(db: Session) -> None:
    db.add(
        LenderORM(
            id=1,
            name="Lender A",
            slug="lender-a",
            capital_base=10_000_000,
        )
    )
    db.add(
        PortfolioORM(
            id=1,
            name="Main",
            lender_id=1,
            capital_allocation=5_000_000,
        )
    )
    db.flush()


def _add_client(
    db: Session,
    *,
    client_id: int,
    industry: str,
    client_name: str | None = None,
) -> None:
    db.add(
        ClientORM(
            id=client_id,
            name=client_name or f"Client {client_id}",
            industry=industry,
            credit_limit=1_000_000,
            lender_id=1,
            portfolio_id=1,
        )
    )
    db.flush()


def _add_deal_position(
    db: Session,
    *,
    client_id: int,
    deal_id: int,
    position_id: int,
    deal_name: str,
    value: float,
) -> None:
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


def _add_client_deal_position(
    db: Session,
    *,
    client_id: int,
    deal_id: int,
    position_id: int,
    industry: str,
    deal_name: str,
    value: float,
    client_name: str | None = None,
) -> None:
    existing = db.get(ClientORM, client_id)
    if existing is None:
        _add_client(
            db,
            client_id=client_id,
            industry=industry,
            client_name=client_name,
        )
    _add_deal_position(
        db,
        client_id=client_id,
        deal_id=deal_id,
        position_id=position_id,
        deal_name=deal_name,
        value=value,
    )


def test_get_portfolio_summary_aggregates_exposure_and_utilization(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolio(db_session)
    _add_client_deal_position(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        industry="Technology",
        deal_name="Tech Loan A",
        value=500_000,
    )
    _add_client_deal_position(
        db_session,
        client_id=10,
        deal_id=101,
        position_id=2,
        industry="Technology",
        deal_name="Tech Loan B",
        value=300_000,
    )
    _add_client_deal_position(
        db_session,
        client_id=11,
        deal_id=102,
        position_id=3,
        industry="Manufacturing",
        deal_name="Factory Loan",
        value=200_000,
    )
    db_session.commit()

    summary = get_portfolio_summary(db_session, portfolio_id=1)

    assert summary["portfolio_id"] == 1
    assert summary["portfolio_name"] == "Main"
    assert summary["capital_allocation"] == 5_000_000
    assert summary["total_exposure"] == 1_000_000
    assert summary["position_count"] == 3
    assert summary["client_count"] == 2
    assert summary["utilization_pct"] == 20.0
    assert [item["industry"] for item in summary["industry_exposure"]] == [
        "Technology",
        "Manufacturing",
    ]
    assert summary["industry_exposure"][0]["value"] == 800_000
    assert summary["industry_exposure"][0]["percentage"] == 80.0
    assert summary["industry_exposure"][1]["value"] == 200_000
    assert summary["industry_exposure"][1]["percentage"] == 20.0


def test_get_portfolio_summary_empty_portfolio(db_session: Session) -> None:
    _seed_lender_and_portfolio(db_session)
    db_session.commit()

    summary = get_portfolio_summary(db_session, portfolio_id=1)

    assert summary["total_exposure"] == 0.0
    assert summary["position_count"] == 0
    assert summary["client_count"] == 0
    assert summary["utilization_pct"] == 0.0
    assert summary["industry_exposure"] == []


def test_get_portfolio_summary_unknown_portfolio_raises(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolio(db_session)
    db_session.commit()

    with pytest.raises(ValueError, match="Portfolio 999 not found"):
        get_portfolio_summary(db_session, portfolio_id=999)


def test_get_portfolio_industry_exposure_uses_client_industry(
    db_session: Session,
) -> None:
    _seed_lender_and_portfolio(db_session)
    _add_client_deal_position(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        industry="Technology",
        deal_name="Tech Loan",
        value=250_000,
    )
    _add_client_deal_position(
        db_session,
        client_id=11,
        deal_id=101,
        position_id=2,
        industry="Retail",
        deal_name="Retail Loan",
        value=750_000,
    )
    db_session.commit()

    exposure = get_portfolio_industry_exposure(db_session, portfolio_id=1)

    assert len(exposure) == 2
    assert exposure[0]["industry"] == "Retail"
    assert exposure[0]["value"] == 750_000
    assert exposure[0]["percentage"] == 75.0
    assert exposure[1]["industry"] == "Technology"
    assert exposure[1]["percentage"] == 25.0


def test_get_portfolio_summary_zero_capital_allocation(db_session: Session) -> None:
    _seed_lender_and_portfolio(db_session)
    portfolio = db_session.get(PortfolioORM, 1)
    assert portfolio is not None
    portfolio.capital_allocation = 0
    _add_client_deal_position(
        db_session,
        client_id=10,
        deal_id=100,
        position_id=1,
        industry="Technology",
        deal_name="Tech Loan",
        value=100_000,
    )
    db_session.commit()

    summary = get_portfolio_summary(db_session, portfolio_id=1)

    assert summary["total_exposure"] == 100_000
    assert summary["utilization_pct"] == 0.0


def _seed_two_lenders(db: Session) -> None:
    db.add_all(
        [
            LenderORM(
                id=1,
                name="Lender A",
                slug="lender-a",
                capital_base=10_000_000,
            ),
            LenderORM(
                id=2,
                name="Lender B",
                slug="lender-b",
                capital_base=10_000_000,
            ),
        ]
    )
    db.flush()


def test_create_portfolio_persists_for_lender(db_session: Session) -> None:
    _seed_two_lenders(db_session)
    db_session.commit()

    record = create_portfolio(
        db_session,
        lender_id=1,
        name=" Growth ",
        capital_allocation=2_500_000,
    )

    assert record.id is not None
    assert record.name == "Growth"
    assert record.lender_id == 1
    assert record.capital_allocation == 2_500_000


def test_create_multiple_portfolios_for_same_lender(db_session: Session) -> None:
    _seed_two_lenders(db_session)
    db_session.commit()

    first = create_portfolio(
        db_session,
        lender_id=1,
        name="Core",
        capital_allocation=1_000_000,
    )
    second = create_portfolio(
        db_session,
        lender_id=1,
        name="Opportunistic",
        capital_allocation=500_000,
    )

    records = get_portfolios_for_lender(db_session, lender_id=1)

    assert [row.id for row in records] == [first.id, second.id]
    assert [row.name for row in records] == ["Core", "Opportunistic"]


def test_get_portfolios_for_lender_excludes_other_lenders(
    db_session: Session,
) -> None:
    _seed_two_lenders(db_session)
    db_session.add(
        PortfolioORM(
            id=1,
            name="Lender A Portfolio",
            lender_id=1,
            capital_allocation=1_000_000,
        )
    )
    db_session.add(
        PortfolioORM(
            id=2,
            name="Lender B Portfolio",
            lender_id=2,
            capital_allocation=2_000_000,
        )
    )
    db_session.commit()

    records = get_portfolios_for_lender(db_session, lender_id=1)

    assert len(records) == 1
    assert records[0].id == 1
    assert records[0].lender_id == 1


def test_create_portfolio_rejects_negative_capital_allocation(
    db_session: Session,
) -> None:
    _seed_two_lenders(db_session)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        create_portfolio(
            db_session,
            lender_id=1,
            name="Invalid",
            capital_allocation=-1,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Capital allocation cannot be negative"


def test_get_portfolio_for_lender_returns_none_for_other_lender(
    db_session: Session,
) -> None:
    _seed_two_lenders(db_session)
    db_session.add(
        PortfolioORM(
            id=1,
            name="Lender B Portfolio",
            lender_id=2,
            capital_allocation=1_000_000,
        )
    )
    db_session.commit()

    assert get_portfolio_for_lender(db_session, portfolio_id=1, lender_id=1) is None
