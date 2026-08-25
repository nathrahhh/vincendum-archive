from __future__ import annotations

import logging
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.deal import DealORM
from app.models.repayment import RepaymentORM

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialBreachInputs:
    """Read-only inputs for the financial repayment-coverage (DSCR) rule.

    Missing data is represented explicitly:
    - ``has_scheduled_debt_service=False`` with ``scheduled_debt_service=0``
      means there are no in-period contractual repayments to cover.
    - ``has_approved_financial=False`` with ``gross_profit=None`` means do not
      invent a gross-profit value.

    ``scheduled_debt_service`` is the sum of ``RepaymentORM.total_due`` for
    APPROVED deals whose ``due_date`` falls in ``[period_start, period_end]``.
    It is contractual debt service for that window only — not lifetime loan
    totals and not Open Banking cash movements.
    """

    lender_id: int
    client_id: int
    gross_profit: float | None
    scheduled_debt_service: float
    period_start: date | None
    period_end: date | None
    has_approved_financial: bool
    has_scheduled_debt_service: bool


def _calendar_month_bounds(month: date) -> tuple[date, date]:
    """Inclusive start/end dates for the calendar month containing ``month``."""
    start = month.replace(day=1)
    end = start.replace(day=monthrange(start.year, start.month)[1])
    return start, end


def _resolve_period(
    *,
    period_start: date | None,
    period_end: date | None,
    financial_month: date | None,
) -> tuple[date, date] | None:
    if period_start is not None or period_end is not None:
        if period_start is None or period_end is None:
            raise ValueError(
                "period_start and period_end must both be provided together"
            )
        if period_start > period_end:
            raise ValueError("period_start must be on or before period_end")
        return period_start, period_end

    if financial_month is not None:
        return _calendar_month_bounds(financial_month)

    return None


def _sum_scheduled_debt_service(
    db: Session,
    *,
    client_id: int,
    period_start: date,
    period_end: date,
) -> tuple[float, bool]:
    """Sum contractual ``total_due`` for APPROVED-deal repayments in the period."""
    totals = db.execute(
        select(RepaymentORM.total_due)
        .join(DealORM, RepaymentORM.deal_id == DealORM.id)
        .where(
            DealORM.client_id == client_id,
            DealORM.status == "APPROVED",
            RepaymentORM.due_date >= period_start,
            RepaymentORM.due_date <= period_end,
        )
    ).scalars().all()

    has_scheduled = len(totals) > 0
    scheduled = float(sum(totals)) if has_scheduled else 0.0
    return scheduled, has_scheduled


def get_financial_breach_inputs(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
    period_start: date | None = None,
    period_end: date | None = None,
) -> FinancialBreachInputs:
    """
    Load gross profit and in-period scheduled debt service for a client.

    Verifies the client belongs to ``lender_id``. Uses the latest approved
    financial by month for gross profit.

    Repayment coverage window:
    - If ``period_start`` and ``period_end`` are both provided, use that range.
    - Otherwise, if an approved financial exists, use that financial's calendar
      month (aligned with monthly gross profit).
    - Otherwise, no period is available and scheduled debt service is empty.

    Does not calculate DSCR ratios or create breaches. Does not use bank
    transactions / Open Banking.
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

    financial_month = financial.month if financial is not None else None
    period = _resolve_period(
        period_start=period_start,
        period_end=period_end,
        financial_month=financial_month,
    )

    if period is None:
        scheduled_debt_service = 0.0
        has_scheduled_debt_service = False
        resolved_start: date | None = None
        resolved_end: date | None = None
    else:
        resolved_start, resolved_end = period
        scheduled_debt_service, has_scheduled_debt_service = (
            _sum_scheduled_debt_service(
                db,
                client_id=client_id,
                period_start=resolved_start,
                period_end=resolved_end,
            )
        )

    logger.info(
        "get_financial_breach_inputs scheduled debt service "
        "client_id=%s lender_id=%s period_start=%s period_end=%s "
        "has_scheduled_debt_service=%s scheduled_debt_service=%s",
        client_id,
        lender_id,
        resolved_start,
        resolved_end,
        has_scheduled_debt_service,
        scheduled_debt_service,
    )

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
            gross_profit=None,
            scheduled_debt_service=scheduled_debt_service,
            period_start=resolved_start,
            period_end=resolved_end,
            has_approved_financial=False,
            has_scheduled_debt_service=has_scheduled_debt_service,
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
        gross_profit=float(financial.gross_profit),
        scheduled_debt_service=scheduled_debt_service,
        period_start=resolved_start,
        period_end=resolved_end,
        has_approved_financial=True,
        has_scheduled_debt_service=has_scheduled_debt_service,
    )
