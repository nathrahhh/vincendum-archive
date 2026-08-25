"""Evaluate the financial DSCR breach rule from pre-aggregated inputs.

Rule:
    DSCR = gross_profit / scheduled_debt_service

Breach when DSCR is strictly below FINANCIAL_DSCR_THRESHOLD.

Does not query the database or create BreachORM rows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.breaches.financial_inputs import FinancialBreachInputs

FINANCIAL_DSCR = "financial_dscr"
FINANCIAL_DSCR_THRESHOLD = 1.2

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialBreachRuleResult:
    """Outcome of evaluating the financial DSCR rule.

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
        "evaluate_financial_dscr result "
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


def evaluate_financial_dscr(
    inputs: FinancialBreachInputs,
) -> FinancialBreachRuleResult:
    """
    Evaluate ``gross_profit / scheduled_debt_service`` against threshold 1.2.

    Returns an unevaluated result when scheduled debt service is missing or
    non-positive, or when approved financial / gross profit is missing. Does
    not round before comparing to the threshold (exactly 1.2 passes).
    """
    if not inputs.has_scheduled_debt_service or inputs.scheduled_debt_service <= 0:
        return _log_rule_result(
            FinancialBreachRuleResult(
                lender_id=inputs.lender_id,
                client_id=inputs.client_id,
                rule=FINANCIAL_DSCR,
                threshold=FINANCIAL_DSCR_THRESHOLD,
                actual_value=None,
                evaluated=False,
                breached=False,
                reason="Scheduled debt service is missing or non-positive",
            )
        )

    if not inputs.has_approved_financial or inputs.gross_profit is None:
        return _log_rule_result(
            FinancialBreachRuleResult(
                lender_id=inputs.lender_id,
                client_id=inputs.client_id,
                rule=FINANCIAL_DSCR,
                threshold=FINANCIAL_DSCR_THRESHOLD,
                actual_value=None,
                evaluated=False,
                breached=False,
                reason="No approved financial",
            )
        )

    dscr = inputs.gross_profit / inputs.scheduled_debt_service
    breached = dscr < FINANCIAL_DSCR_THRESHOLD

    return _log_rule_result(
        FinancialBreachRuleResult(
            lender_id=inputs.lender_id,
            client_id=inputs.client_id,
            rule=FINANCIAL_DSCR,
            threshold=FINANCIAL_DSCR_THRESHOLD,
            actual_value=dscr,
            evaluated=True,
            breached=breached,
            reason=None,
        )
    )
