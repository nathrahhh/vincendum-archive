"""Portfolio management and monitoring services."""

from __future__ import annotations

from typing import TypedDict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioORM
from app.models.schemas import PortfolioRecord
from app.services.position_service import (
    PortfolioPositionDetail,
    get_positions_for_portfolio,
)


class PortfolioIndustryExposure(TypedDict):
    industry: str
    value: float
    percentage: float


class PortfolioSummary(TypedDict):
    portfolio_id: int
    portfolio_name: str
    capital_allocation: float
    total_exposure: float
    position_count: int
    client_count: int
    utilization_pct: float
    industry_exposure: list[PortfolioIndustryExposure]


def _to_portfolio_record(portfolio: PortfolioORM) -> PortfolioRecord:
    return PortfolioRecord(
        id=portfolio.id,
        name=portfolio.name,
        lender_id=portfolio.lender_id,
        capital_allocation=float(portfolio.capital_allocation),
    )


def _get_portfolio_or_raise(db: Session, portfolio_id: int) -> PortfolioORM:
    portfolio = db.get(PortfolioORM, portfolio_id)
    if portfolio is None:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    return portfolio


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
    if capital_allocation < 0:
        raise HTTPException(
            status_code=400,
            detail="Capital allocation cannot be negative",
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


def _build_industry_exposure(
    positions: list[PortfolioPositionDetail],
) -> list[PortfolioIndustryExposure]:
    """Aggregate ``positions`` by ``ClientORM.industry``."""
    if not positions:
        return []

    by_industry: dict[str, float] = {}
    for position in positions:
        industry = position["client_industry"]
        by_industry[industry] = by_industry.get(industry, 0.0) + position["value"]

    total_exposure = sum(by_industry.values())
    exposure = [
        PortfolioIndustryExposure(
            industry=industry,
            value=round(amount, 4),
            percentage=(
                0.0
                if total_exposure == 0
                else round((amount / total_exposure) * 100, 4)
            ),
        )
        for industry, amount in by_industry.items()
    ]
    exposure.sort(key=lambda item: item["value"], reverse=True)
    return exposure


def get_portfolio_industry_exposure(
    db: Session,
    portfolio_id: int,
) -> list[PortfolioIndustryExposure]:
    """
    Aggregate position values by client industry for ``portfolio_id``.

    Percentages are ``industry exposure / total portfolio exposure * 100``.
    Industries are sorted by exposure descending.
    """
    positions = get_positions_for_portfolio(db, portfolio_id)
    return _build_industry_exposure(positions)


def get_portfolio_summary(
    db: Session,
    portfolio_id: int,
) -> PortfolioSummary:
    """
    Return portfolio monitoring metrics for ``portfolio_id``.

    Exposure and industry breakdowns are derived from positions linked through
    Deal → Client where ``clients.portfolio_id`` matches the portfolio.
    Utilization uses the portfolio's ``capital_allocation``.
    """
    portfolio = _get_portfolio_or_raise(db, portfolio_id)
    positions = get_positions_for_portfolio(db, portfolio_id)

    total_exposure = round(sum(position["value"] for position in positions), 4)
    client_count = len({position["client_id"] for position in positions})
    capital_allocation = float(portfolio.capital_allocation)
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
        industry_exposure=_build_industry_exposure(positions),
    )
