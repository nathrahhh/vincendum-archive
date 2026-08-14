"""Persist already-evaluated financial breach rule results.

Does not evaluate rules, query related entities, or commit transactions.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.breach import BreachORM
from app.services.breaches.financial_breach_rule import FinancialBreachRuleResult

logger = logging.getLogger(__name__)


def persist_financial_breach_result(
    db: Session,
    result: FinancialBreachRuleResult,
    *,
    detail: str,
) -> BreachORM | None:
    """
    Persist a financial breach when the rule was evaluated and breached.

    Returns ``None`` for unevaluated or passing results. Flushes the new row
    so the caller controls commit/rollback.
    """
    if not result.evaluated:
        logger.info(
            "persist_financial_breach_result skipped not evaluated "
            "lender_id=%s client_id=%s rule=%s reason=%r",
            result.lender_id,
            result.client_id,
            result.rule,
            result.reason,
        )
        return None

    if not result.breached:
        logger.info(
            "persist_financial_breach_result skipped no breach "
            "lender_id=%s client_id=%s rule=%s actual_value=%s threshold=%s",
            result.lender_id,
            result.client_id,
            result.rule,
            result.actual_value,
            result.threshold,
        )
        return None

    breach = BreachORM(
        lender_id=result.lender_id,
        client_id=result.client_id,
        rule=result.rule,
        reason=result.reason,
        threshold=result.threshold,
        actual_value=result.actual_value,
        detail=detail,
        status="OPEN",
        resolved_by=None,
        resolved_at=None,
    )
    db.add(breach)
    db.flush()
    logger.info(
        "persist_financial_breach_result created new breach "
        "lender_id=%s client_id=%s rule=%s breach_id=%s status=%s",
        result.lender_id,
        result.client_id,
        result.rule,
        breach.id,
        breach.status,
    )
    return breach
