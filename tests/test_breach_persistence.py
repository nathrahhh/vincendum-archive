from unittest.mock import MagicMock

from app.services.breaches.breach_persistence import persist_financial_breach_result
from app.services.breaches.financial_breach_rule import (
    FINANCIAL_GROSS_PROFIT_RATIO,
    FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
    FinancialBreachRuleResult,
)


def _result(
    *,
    evaluated: bool,
    breached: bool,
    actual_value: float | None,
    reason: str | None = None,
) -> FinancialBreachRuleResult:
    return FinancialBreachRuleResult(
        lender_id=10,
        client_id=20,
        rule=FINANCIAL_GROSS_PROFIT_RATIO,
        threshold=FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
        actual_value=actual_value,
        evaluated=evaluated,
        breached=breached,
        reason=reason,
    )


def test_unevaluated_result_returns_none_and_creates_no_row():
    db = MagicMock()
    result = _result(
        evaluated=False,
        breached=False,
        actual_value=None,
        reason="No approved deals",
    )

    persisted = persist_financial_breach_result(
        db,
        result,
        detail="should not persist",
    )

    assert persisted is None
    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_evaluated_passing_result_returns_none_and_creates_no_row():
    db = MagicMock()
    result = _result(
        evaluated=True,
        breached=False,
        actual_value=1.2,
    )

    persisted = persist_financial_breach_result(
        db,
        result,
        detail="should not persist",
    )

    assert persisted is None
    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_evaluated_breached_result_creates_breach_orm():
    db = MagicMock()
    detail = "Gross profit ratio below threshold"
    result = _result(
        evaluated=True,
        breached=True,
        actual_value=1.0,
        reason="Financial gross profit ratio breached",
    )

    persisted = persist_financial_breach_result(db, result, detail=detail)

    assert persisted is not None
    db.add.assert_called_once_with(persisted)
    db.flush.assert_called_once_with()
    db.commit.assert_not_called()

    assert persisted.lender_id == 10
    assert persisted.client_id == 20
    assert persisted.rule == FINANCIAL_GROSS_PROFIT_RATIO
    assert persisted.threshold == FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD
    assert persisted.actual_value == 1.0
    assert persisted.status == "OPEN"
    assert persisted.detail == detail
    assert persisted.reason == "Financial gross profit ratio breached"
    assert persisted.resolved_by is None
    assert persisted.resolved_at is None
