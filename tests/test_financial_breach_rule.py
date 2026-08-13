from app.services.breaches.financial_breach_rule import (
    FINANCIAL_GROSS_PROFIT_RATIO,
    FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD,
    evaluate_financial_gross_profit_ratio,
)
from app.services.breaches.financial_inputs import FinancialBreachInputs


def _inputs(
    *,
    total_deal_value: float,
    gross_profit: float | None,
    has_approved_deals: bool,
    has_approved_financial: bool,
) -> FinancialBreachInputs:
    return FinancialBreachInputs(
        lender_id=1,
        client_id=2,
        total_deal_value=total_deal_value,
        gross_profit=gross_profit,
        has_approved_deals=has_approved_deals,
        has_approved_financial=has_approved_financial,
    )


def test_passing_ratio_at_threshold():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=10_000_000,
            gross_profit=120_000,
            has_approved_deals=True,
            has_approved_financial=True,
        )
    )

    assert result.rule == FINANCIAL_GROSS_PROFIT_RATIO
    assert result.threshold == FINANCIAL_GROSS_PROFIT_RATIO_THRESHOLD
    assert result.actual_value == 1.2
    assert result.evaluated is True
    assert result.breached is False


def test_breach_ratio_below_threshold():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=10_000_000,
            gross_profit=100_000,
            has_approved_deals=True,
            has_approved_financial=True,
        )
    )

    assert result.actual_value == 1.0
    assert result.evaluated is True
    assert result.breached is True


def test_just_below_threshold_is_breach():
    # 119_999 / (10_000_000 * 0.01) = 1.19999... < 1.2
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=10_000_000,
            gross_profit=119_999,
            has_approved_deals=True,
            has_approved_financial=True,
        )
    )

    assert result.evaluated is True
    assert result.actual_value is not None
    assert result.actual_value < 1.2
    assert result.breached is True


def test_zero_total_deal_value_is_unevaluated():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=0,
            gross_profit=120_000,
            has_approved_deals=True,
            has_approved_financial=True,
        )
    )

    assert result.evaluated is False
    assert result.breached is False
    assert result.actual_value is None


def test_negative_total_deal_value_is_unevaluated():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=-1_000,
            gross_profit=120_000,
            has_approved_deals=True,
            has_approved_financial=True,
        )
    )

    assert result.evaluated is False
    assert result.breached is False
    assert result.actual_value is None


def test_no_approved_deals_is_unevaluated():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=0,
            gross_profit=120_000,
            has_approved_deals=False,
            has_approved_financial=True,
        )
    )

    assert result.evaluated is False
    assert result.breached is False
    assert result.actual_value is None


def test_no_approved_financial_is_unevaluated():
    result = evaluate_financial_gross_profit_ratio(
        _inputs(
            total_deal_value=10_000_000,
            gross_profit=None,
            has_approved_deals=True,
            has_approved_financial=False,
        )
    )

    assert result.evaluated is False
    assert result.breached is False
    assert result.actual_value is None
