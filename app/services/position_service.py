"""Read-only queries for positions derived through Deal → Client → Portfolio."""

from __future__ import annotations

from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM


class PortfolioPositionDetail(TypedDict):
    position_id: int
    value: float
    deal_id: int
    deal_name: str
    client_id: int
    client_name: str
    client_industry: str


def _portfolio_positions_query(portfolio_id: int):
    return (
        select(
            PositionORM.id,
            PositionORM.value,
            DealORM.id,
            DealORM.name,
            ClientORM.id,
            ClientORM.name,
            ClientORM.industry,
        )
        .select_from(PositionORM)
        .join(DealORM, PositionORM.deal_id == DealORM.id)
        .join(ClientORM, DealORM.client_id == ClientORM.id)
        .where(ClientORM.portfolio_id == portfolio_id)
        .order_by(PositionORM.id)
    )


def get_positions_for_portfolio(
    db: Session,
    portfolio_id: int,
) -> list[PortfolioPositionDetail]:
    """
    Return all positions belonging to ``portfolio_id``.

    Portfolio membership is derived via Position → Deal → Client → Portfolio
    (``clients.portfolio_id``), not stored on ``PositionORM``.
    """
    rows = db.execute(_portfolio_positions_query(portfolio_id)).all()
    return [
        PortfolioPositionDetail(
            position_id=position_id,
            value=float(value),
            deal_id=deal_id,
            deal_name=deal_name,
            client_id=client_id,
            client_name=client_name,
            client_industry=client_industry,
        )
        for (
            position_id,
            value,
            deal_id,
            deal_name,
            client_id,
            client_name,
            client_industry,
        ) in rows
    ]
