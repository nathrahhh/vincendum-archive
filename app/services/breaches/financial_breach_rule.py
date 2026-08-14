"""Evaluate the first financial breach rule from pre-aggregated inputs.

Rule:
    gross_profit / (total_approved_deal_value * FINANCIAL_GROSS_PROFIT_RATE)

Breach when the ratio is strictly below FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD.

Does not query the database or create BreachORM rows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.breaches.financial_inputs import FinancialBreachInputs

FINANCIAL_GROSS_PROFIT_RATIO = "financial_gross_profit_ratio"
FINANCIAL_GROSS_PROFIT_RATE = 0.01
FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD = 1.2

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialBreachRuleResult:
    """Outcome of evaluating the financial gross-profit ratio rule.

    When ``evaluated`` is False, ``actual_value`` is None and ``breached`` is
    False — the rule was skipped due to missing inputs, not because it passed.
    """

    lender_id: int
    client_id: int
    rule: str
    threshold: float
    actual_value: float | None
    evaluated: bool
    breached: bool
    reason: str | None = None


def _log_rule_result(result: FinancialBreachRuleResult) -> FinancialBreachRuleResult:
    logger.info(
        "evaluate_financial_gross_profit_ratio result "
        "lender_id=%s client_id=%s rule=%s evaluated=%s breached=%s "
        "actual_value=%s threshold=%s reason=%r",
        result.lender_id,
        result.client_id,
        result.rule,
        result.evaluated,
        result.breached,
        result.actual_value,
        result.threshold,
        result.reason,
    )
    return result


def evaluate_financial_gross_profit_ratio(
    inputs: FinancialBreachInputs,
) -> FinancialBreachRuleResult:
    """
    Evaluate ``gross_profit / (total_deal_value * rate)`` against threshold 1.2.

    Returns an unevaluated result when approved deals or approved financials
    are missing, or when approved deal value is zero/negative. Does not round
    before comparing to the threshold.
    """
    if not inputs.has_approved_deals:
        return _log_rule_result(
            FinancialBreachRuleResult(
                lender_id=inputs.lender_id,
                client_id=inputs.client_id,
                rule=FINANCIAL_GROSS_PROFIT_RATIO,
                threshold=FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
                actual_value=None,
                evaluated=False,
                breached=False,
                reason="No approved deals",
            )
        )

    if inputs.total_deal_value <= 0:
        return _log_rule_result(
            FinancialBreachRuleResult(
                lender_id=inputs.lender_id,
                client_id=inputs.client_id,
                rule=FINANCIAL_GROSS_PROFIT_RATIO,
                threshold=FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
                actual_value=None,
                evaluated=False,
                breached=False,
                reason="Approved deal value is zero or negative",
            )
        )

    if not inputs.has_approved_financial or inputs.gross_profit is None:
        return _log_rule_result(
            FinancialBreachRuleResult(
                lender_id=inputs.lender_id,
                client_id=inputs.client_id,
                rule=FINANCIAL_GROSS_PROFIT_RATIO,
                threshold=FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
                actual_value=None,
                evaluated=False,
                breached=False,
                reason="No approved financial",
            )
        )

    denominator = inputs.total_deal_value * FINANCIAL_GROSS_PROFIT_RATE
    ratio = inputs.gross_profit / denominator
    breached = ratio < FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD

    return _log_rule_result(
        FinancialBreachRuleResult(
            lender_id=inputs.lender_id,
            client_id=inputs.client_id,
            rule=FINANCIAL_GROSS_PROFIT_RATIO,
            threshold=FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
            actual_value=ratio,
            evaluated=True,
            breached=breached,
            reason=None,
        )
    )
