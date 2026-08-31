"""Industry exposure aggregation for a lender's portfolios."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.portfolio import PortfolioORM
from app.models.position import PositionORM
from app.models.schemas import IndustryExposure


def get_industry_exposure(
    db: Session,
    lender_id: int,
) -> list[IndustryExposure]:
    """
    Aggregate position values by client industry for ``lender_id``.

    Percentages are ``industry exposure / total lender exposure * 100``.
    Industries are sorted by exposure descending. Positions without a linked
    client are excluded. An empty portfolio returns ``[]``.
    """
    rows = db.execute(
        select(ClientORM.industry, PositionORM.value)
        .select_from(PortfolioORM)
        .join(ClientORM, ClientORM.portfolio_id == PortfolioORM.id)
        .join(DealORM, DealORM.client_id == ClientORM.id)
        .join(PositionORM, PositionORM.deal_id == DealORM.id)
        .where(PortfolioORM.lender_id == lender_id)
    ).all()

    if not rows:
        return []

    by_industry: dict[str, float] = {}
    for industry, value in rows:
        by_industry[industry] = by_industry.get(industry, 0.0) + float(value)

    total_exposure = sum(by_industry.values())

    exposure = [
        IndustryExposure(
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
    exposure.sort(key=lambda item: item.value, reverse=True)
    return exposure
