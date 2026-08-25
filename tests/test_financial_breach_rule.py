from datetime import date

from app.services.breaches.financial_breach_rule import (
    FINANCIAL_DSCR,
    FINANCIAL_DSCR_THRESHOLD,
    evaluate_financial_dscr,
)
from app.services.breaches.financial_inputs import FinancialBreachInputs


def _inputs(
    *,
    gross_profit: float | None,
    scheduled_debt_service: float,
    has_scheduled_debt_service: bool,
    has_approved_financial: bool,
    period_start: date | None = date(2027, 4, 1),
    period_end: date | None = date(2027, 4, 30),
) -> FinancialBreachInputs:
    return FinancialBreachInputs(
        lender_id=1,
        client_id=2,
        gross_profit=gross_profit,
        scheduled_debt_service=scheduled_debt_service,
        period_start=period_start,
        period_end=period_end,
        has_approved_financial=has_approved_financial,
        has_scheduled_debt_service=has_scheduled_debt_service,
    )


def test_dscr_exactly_at_threshold_passes():
    # 1200 / 1000 = 1.2
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_200,
            scheduled_debt_service=1_000,
            has_scheduled_debt_service=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.threshold == FINANCIAL_DSCR_THRESHOLD
    assert result.actual_value == 1.2
    assert result.evaluated is True
    assert result.breached is False


def test_dscr_above_threshold_passes():
    # 1500 / 1000 = 1.5
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_500,
            scheduled_debt_service=1_000,
            has_scheduled_debt_service=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value == 1.5
    assert result.evaluated is True
    assert result.breached is False


def test_dscr_below_threshold_breaches():
    # 1000 / 1000 = 1.0
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_000,
            scheduled_debt_service=1_000,
            has_scheduled_debt_service=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value == 1.0
    assert result.evaluated is True
    assert result.breached is True


def test_zero_scheduled_debt_service_is_unevaluated():
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_200,
            scheduled_debt_service=0,
            has_scheduled_debt_service=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value is None
    assert result.evaluated is False
    assert result.breached is False


def test_negative_scheduled_debt_service_is_unevaluated():
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_200,
            scheduled_debt_service=-1_000,
            has_scheduled_debt_service=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value is None
    assert result.evaluated is False
    assert result.breached is False


def test_no_scheduled_debt_service_is_unevaluated():
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=1_200,
            scheduled_debt_service=0,
            has_scheduled_debt_service=False,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value is None
    assert result.evaluated is False
    assert result.breached is False


def test_missing_gross_profit_is_unevaluated():
    result = evaluate_financial_dscr(
        _inputs(
            gross_profit=None,
            scheduled_debt_service=1_000,
            has_scheduled_debt_service=True,
            has_approved_financial=False,
        )
    )

    assert result.rule == FINANCIAL_DSCR
    assert result.actual_value is None
    assert result.evaluated is False
    assert result.breached is False
