"""Persist already-evaluated financial breach rule results.

Does not evaluate rules, query related entities, or commit transactions.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.breach import BreachORM
from app.services.breaches.financial_breach_rule import FinancialBreachRuleResult


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
    if not result.evaluated or not result.breached:
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
    return breach
