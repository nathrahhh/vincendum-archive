from datetime import date
from unittest.mock import MagicMock, patch

from app.services.breaches.financial_breach_rule import (
    FINANCIAL_DSCR,
    FINANCIAL_DSCR_THRESHOLD,
    FinancialBreachRuleResult,
)
from app.services.breaches.financial_breach_service import (
    evaluate_and_persist_financial_breach,
)
from app.services.breaches.financial_inputs import FinancialBreachInputs


MODULE = "app.services.breaches.financial_breach_service"


def _inputs(
    *,
    scheduled_debt_service: float = 100_000,
    gross_profit: float | None = 100_000,
    has_scheduled_debt_service: bool = True,
    has_approved_financial: bool = True,
) -> FinancialBreachInputs:
    return FinancialBreachInputs(
        lender_id=10,
        client_id=20,
        gross_profit=gross_profit,
        scheduled_debt_service=scheduled_debt_service,
        period_start=date(2027, 4, 1),
        period_end=date(2027, 4, 30),
        has_approved_financial=has_approved_financial,
        has_scheduled_debt_service=has_scheduled_debt_service,
    )


def test_breached_result_flows_through_and_returns_persisted_row():
    db = MagicMock()
    inputs = _inputs()
    rule_result = FinancialBreachRuleResult(
        lender_id=10,
        client_id=20,
        rule=FINANCIAL_DSCR,
        threshold=FINANCIAL_DSCR_THRESHOLD,
        actual_value=1.0,
        evaluated=True,
        breached=True,
        reason=None,
    )
    persisted = MagicMock(name="BreachORM")

    with (
        patch(f"{MODULE}.get_financial_breach_inputs", return_value=inputs) as get_inputs,
        patch(
            f"{MODULE}.evaluate_financial_dscr",
            return_value=rule_result,
        ) as evaluate,
        patch(
            f"{MODULE}.persist_financial_breach_result",
            return_value=persisted,
        ) as persist,
    ):
        result = evaluate_and_persist_financial_breach(
            db,
            lender_id=10,
            client_id=20,
            financial_id=301,
        )

    get_inputs.assert_called_once_with(
        db,
        lender_id=10,
        client_id=20,
    )
    evaluate.assert_called_once_with(inputs)
    persist.assert_called_once()
    assert persist.call_args.args[0] is db
    assert persist.call_args.args[1] is rule_result
    assert "Gross profit: 100000" in persist.call_args.kwargs["detail"]
    assert "Scheduled debt service: 100000" in persist.call_args.kwargs["detail"]
    assert "DSCR: 1.0" in persist.call_args.kwargs["detail"]
    assert "Threshold: 1.2" in persist.call_args.kwargs["detail"]
    assert result is persisted


def test_unevaluated_result_is_passed_to_persistence_and_returns_none():
    db = MagicMock()
    inputs = _inputs(
        has_scheduled_debt_service=False,
        scheduled_debt_service=0,
        gross_profit=None,
        has_approved_financial=False,
    )
    rule_result = FinancialBreachRuleResult(
        lender_id=10,
        client_id=20,
        rule=FINANCIAL_DSCR,
        threshold=FINANCIAL_DSCR_THRESHOLD,
        actual_value=None,
        evaluated=False,
        breached=False,
        reason="No scheduled debt service",
    )

    with (
        patch(f"{MODULE}.get_financial_breach_inputs", return_value=inputs),
        patch(
            f"{MODULE}.evaluate_financial_dscr",
            return_value=rule_result,
        ),
        patch(
            f"{MODULE}.persist_financial_breach_result",
            return_value=None,
        ) as persist,
    ):
        result = evaluate_and_persist_financial_breach(
            db,
            lender_id=10,
            client_id=20,
            financial_id=302,
        )

    persist.assert_called_once()
    assert persist.call_args.args[1] is rule_result
    assert persist.call_args.kwargs["detail"] == "No scheduled debt service"
    assert result is None


def test_passing_result_is_passed_to_persistence_and_returns_none():
    db = MagicMock()
    # 120_000 / 100_000 = 1.2
    inputs = _inputs(gross_profit=120_000, scheduled_debt_service=100_000)
    rule_result = FinancialBreachRuleResult(
        lender_id=10,
        client_id=20,
        rule=FINANCIAL_DSCR,
        threshold=FINANCIAL_DSCR_THRESHOLD,
        actual_value=1.2,
        evaluated=True,
        breached=False,
        reason=None,
    )

    with (
        patch(f"{MODULE}.get_financial_breach_inputs", return_value=inputs),
        patch(
            f"{MODULE}.evaluate_financial_dscr",
            return_value=rule_result,
        ),
        patch(
            f"{MODULE}.persist_financial_breach_result",
            return_value=None,
        ) as persist,
    ):
        result = evaluate_and_persist_financial_breach(
            db,
            lender_id=10,
            client_id=20,
            financial_id=302,
        )

    persist.assert_called_once()
    assert persist.call_args.args[1] is rule_result
    assert "Gross profit: 120000" in persist.call_args.kwargs["detail"]
    assert "Scheduled debt service: 100000" in persist.call_args.kwargs["detail"]
    assert "DSCR: 1.2" in persist.call_args.kwargs["detail"]
    assert "Threshold: 1.2" in persist.call_args.kwargs["detail"]
    assert result is None
