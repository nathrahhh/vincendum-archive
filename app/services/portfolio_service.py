"""Portfolio management and monitoring services."""

from __future__ import annotations

from typing import TypedDict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.portfolio import PortfolioORM
from app.models.schemas import PortfolioRecord
from app.services.lender_service import validate_portfolio_capital_allocation
from app.services.position_service import get_positions_for_portfolio


class PortfolioSummary(TypedDict):
    portfolio_id: int
    portfolio_name: str
    capital_allocation: float
    total_exposure: float
    position_count: int
    client_count: int
    utilization_pct: float
    remaining_capacity: float


def _to_portfolio_record(portfolio: PortfolioORM) -> PortfolioRecord:
    return PortfolioRecord(
        id=portfolio.id,
        name=portfolio.name,
        lender_id=portfolio.lender_id,
        capital_allocation=float(portfolio.capital_allocation),
    )


def get_portfolio_for_lender(
    db: Session,
    portfolio_id: int,
    lender_id: int,
) -> PortfolioORM | None:
    """Return a portfolio when it belongs to ``lender_id``."""
    return db.execute(
        select(PortfolioORM).where(
            PortfolioORM.id == portfolio_id,
            PortfolioORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()


def _get_portfolio_for_lender_or_raise(
    db: Session,
    portfolio_id: int,
    lender_id: int,
) -> PortfolioORM:
    """Return an owned portfolio or raise ``ValueError`` when not found."""
    portfolio = get_portfolio_for_lender(db, portfolio_id, lender_id)
    if portfolio is None:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    return portfolio


def create_portfolio(
    db: Session,
    *,
    lender_id: int,
    name: str,
    capital_allocation: float,
) -> PortfolioRecord:
    """Create a portfolio owned by ``lender_id``."""
    cleaned_name = name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Portfolio name is required")

    validate_portfolio_capital_allocation(
        db,
        lender_id,
        capital_allocation,
    )

    portfolio = PortfolioORM(
        name=cleaned_name,
        lender_id=lender_id,
        capital_allocation=capital_allocation,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return _to_portfolio_record(portfolio)


def update_portfolio(
    db: Session,
    *,
    portfolio_id: int,
    lender_id: int,
    name: str | None = None,
    capital_allocation: float | None = None,
) -> PortfolioRecord:
    """Update an owned portfolio's name and/or capital allocation."""
    portfolio = _get_portfolio_for_lender_or_raise(db, portfolio_id, lender_id)

    if name is not None:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise HTTPException(status_code=400, detail="Portfolio name is required")
        portfolio.name = cleaned_name

    if capital_allocation is not None:
        validate_portfolio_capital_allocation(
            db,
            lender_id,
            capital_allocation,
            exclude_portfolio_id=portfolio_id,
        )
        portfolio.capital_allocation = capital_allocation

    db.commit()
    db.refresh(portfolio)
    return _to_portfolio_record(portfolio)


def get_portfolios_for_lender(
    db: Session,
    lender_id: int,
) -> list[PortfolioRecord]:
    """Return all portfolios owned by ``lender_id``, ordered by id ascending."""
    rows = db.execute(
        select(PortfolioORM)
        .where(PortfolioORM.lender_id == lender_id)
        .order_by(PortfolioORM.id.asc())
    ).scalars().all()
    return [_to_portfolio_record(row) for row in rows]


def get_portfolio_summary(
    db: Session,
    portfolio_id: int,
    lender_id: int,
) -> PortfolioSummary:
    """
    Return portfolio monitoring metrics for ``portfolio_id`` owned by ``lender_id``.

    Exposure is derived from positions linked through Deal → Client where
    ``clients.portfolio_id`` matches the portfolio.
    Utilization uses the portfolio's ``capital_allocation``.
    """
    portfolio = _get_portfolio_for_lender_or_raise(db, portfolio_id, lender_id)
    positions = get_positions_for_portfolio(db, portfolio_id)

    credit_limits = db.execute(
        select(ClientORM.credit_limit).where(
            ClientORM.portfolio_id == portfolio_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalars().all()
    total_credit_limit = sum(float(credit_limit or 0) for credit_limit in credit_limits)

    total_exposure = round(sum(position["value"] for position in positions), 4)
    client_count = len({position["client_id"] for position in positions})
    capital_allocation = float(portfolio.capital_allocation)
    remaining_capacity = round(capital_allocation - total_credit_limit, 4)
    utilization_pct = (
        0.0
        if capital_allocation <= 0
        else round((total_exposure / capital_allocation) * 100, 4)
    )

    return PortfolioSummary(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        capital_allocation=capital_allocation,
        total_exposure=total_exposure,
        position_count=len(positions),
        client_count=client_count,
        utilization_pct=utilization_pct,
        remaining_capacity=remaining_capacity,
    )
