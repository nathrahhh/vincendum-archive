from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.deal import DealORM

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialBreachInputs:
    """Read-only inputs for the first financial breach rule.

    Missing data is represented explicitly:
    - ``has_approved_deals=False`` with ``total_deal_value=0`` means do not
      divide by zero or invent deal exposure.
    - ``has_approved_financial=False`` with ``gross_profit=None`` means do not
      invent a gross-profit value.
    """

    lender_id: int
    client_id: int
    total_deal_value: float
    gross_profit: float | None
    has_approved_deals: bool
    has_approved_financial: bool


def get_financial_breach_inputs(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
) -> FinancialBreachInputs:
    """
    Aggregate approved-deal value and latest approved gross profit for a client.

    Verifies the client belongs to ``lender_id``. Uses the latest approved
    financial by month for the client. Does not calculate ratios or create
    breaches.
    """
    client = db.execute(
        select(ClientORM).where(
            ClientORM.id == client_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client {client_id} not found",
        )
    logger.info(
        "get_financial_breach_inputs tenant check succeeded "
        "client_id=%s lender_id=%s",
        client_id,
        lender_id,
    )

    approved_deal_values = db.execute(
        select(DealORM.value).where(
            DealORM.client_id == client_id,
            DealORM.status == "APPROVED",
        )
    ).scalars().all()
    has_approved_deals = len(approved_deal_values) > 0
    total_deal_value = float(sum(approved_deal_values)) if has_approved_deals else 0.0
    logger.info(
        "get_financial_breach_inputs approved deals aggregated "
        "client_id=%s lender_id=%s "
        "has_approved_deals=%s deal_count=%s total_deal_value=%s",
        client_id,
        lender_id,
        has_approved_deals,
        len(approved_deal_values),
        total_deal_value,
    )

    logger.info(
        "get_financial_breach_inputs querying latest approved financial "
        "client_id=%s lender_id=%s",
        client_id,
        lender_id,
    )
    financial = db.execute(
        select(ClientFinancialORM)
        .where(
            ClientFinancialORM.client_id == client_id,
            ClientFinancialORM.status == "APPROVED",
        )
        .order_by(ClientFinancialORM.month.desc())
        .limit(1)
    ).scalar_one_or_none()

    if financial is None:
        logger.info(
            "get_financial_breach_inputs approved financial not found "
            "client_id=%s lender_id=%s",
            client_id,
            lender_id,
        )
        return FinancialBreachInputs(
            lender_id=lender_id,
            client_id=client_id,
            total_deal_value=total_deal_value,
            gross_profit=None,
            has_approved_deals=has_approved_deals,
            has_approved_financial=False,
        )

    logger.info(
        "get_financial_breach_inputs approved financial found "
        "client_id=%s lender_id=%s financial_id=%s month=%s has_gross_profit=%s",
        client_id,
        lender_id,
        financial.id,
        financial.month,
        financial.gross_profit is not None,
    )
    return FinancialBreachInputs(
        lender_id=lender_id,
        client_id=client_id,
        total_deal_value=total_deal_value,
        gross_profit=float(financial.gross_profit),
        has_approved_deals=has_approved_deals,
        has_approved_financial=True,
    )
