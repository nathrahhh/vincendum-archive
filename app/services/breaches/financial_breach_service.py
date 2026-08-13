"""Orchestrate financial gross-profit breach evaluation and persistence.

Wires input aggregation → rule evaluation → persistence.
Does not calculate ratios, query deals/financials, or commit transactions.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.breach import BreachORM
from app.services.breaches.breach_persistence import persist_financial_breach_result
from app.services.breaches.financial_breach_rule import (
    FINANCIAL_GROSS_PROFIT_RATE,
    FinancialBreachRuleResult,
    evaluate_financial_gross_profit_ratio,
)
from app.services.breaches.financial_inputs import (
    FinancialBreachInputs,
    get_financial_breach_inputs,
)


def _detail_for_result(
    inputs: FinancialBreachInputs,
    result: FinancialBreachRuleResult,
) -> str:
    if not result.evaluated:
        return result.reason or "Financial gross-profit ratio was not evaluated."

    rate_pct = FINANCIAL_GROSS_PROFIT_RATE * 100
    return (
        f"Gross profit: {inputs.gross_profit}, "
        f"approved deal value: {inputs.total_deal_value}, "
        f"rate: {rate_pct:g}%, "
        f"ratio: {result.actual_value}, "
        f"threshold: {result.threshold}."
    )


def evaluate_and_persist_financial_breach(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
) -> BreachORM | None:
    """
    Aggregate inputs, evaluate the financial gross-profit rule, and persist
    a breach when the rule is evaluated and breached.
    """
    inputs = get_financial_breach_inputs(
        db,
        lender_id=lender_id,
        client_id=client_id,
    )
    result = evaluate_financial_gross_profit_ratio(inputs)
    detail = _detail_for_result(inputs, result)
    return persist_financial_breach_result(db, result, detail=detail)
