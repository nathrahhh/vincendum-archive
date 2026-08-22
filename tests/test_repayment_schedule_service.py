"""Unit tests for fixed-rate monthly amortizing repayment schedules."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.repayment_schedule_service import (
    RepaymentScheduleItem,
    generate_repayment_schedule,
)


def test_schedule_length_equals_term_months() -> None:
    schedule = generate_repayment_schedule(
        principal_amount=100_000.0,
        annual_interest_rate=7.0,
        term_months=36,
        first_payment_date=date(2026, 1, 15),
    )

    assert len(schedule) == 36


def test_normal_fixed_rate_amortizing_loan() -> None:
    schedule = generate_repayment_schedule(
        principal_amount=100_000.0,
        annual_interest_rate=7.0,
        term_months=12,
        first_payment_date=date(2026, 1, 1),
    )

    assert len(schedule) == 12
    assert schedule[0].due_date == date(2026, 1, 1)
    assert schedule[1].due_date == date(2026, 2, 1)
    assert schedule[-1].due_date == date(2026, 12, 1)

    # First payment: interest on full principal, principal reduces balance.
    assert schedule[0].interest_due == round(100_000.0 * 0.07 / 12, 2)
    assert schedule[0].principal_due > 0
    assert schedule[0].total_due == round(
        schedule[0].principal_due + schedule[0].interest_due,
        2,
    )

    # Interest declines as principal amortizes.
    assert schedule[-1].interest_due < schedule[0].interest_due


def test_zero_interest_loan() -> None:
    principal = 12_000.0
    schedule = generate_repayment_schedule(
        principal_amount=principal,
        annual_interest_rate=0.0,
        term_months=12,
        first_payment_date=date(2026, 3, 1),
    )

    assert len(schedule) == 12
    assert all(item.interest_due == 0.0 for item in schedule)
    assert all(
        item.total_due == item.principal_due for item in schedule
    )
    assert sum(item.principal_due for item in schedule) == principal


def test_short_three_month_loan() -> None:
    schedule = generate_repayment_schedule(
        principal_amount=9_000.0,
        annual_interest_rate=6.0,
        term_months=3,
        first_payment_date=date(2026, 1, 10),
    )

    assert len(schedule) == 3
    assert [item.due_date for item in schedule] == [
        date(2026, 1, 10),
        date(2026, 2, 10),
        date(2026, 3, 10),
    ]
    assert sum(item.principal_due for item in schedule) == 9_000.0


def test_total_principal_repaid_equals_original() -> None:
    principal = 500_000.0
    schedule = generate_repayment_schedule(
        principal_amount=principal,
        annual_interest_rate=7.0,
        term_months=36,
        first_payment_date=date(2026, 2, 1),
    )

    total_principal = sum(item.principal_due for item in schedule)
    assert total_principal == principal


def test_each_item_principal_plus_interest_equals_total() -> None:
    schedule = generate_repayment_schedule(
        principal_amount=250_000.0,
        annual_interest_rate=5.5,
        term_months=24,
        first_payment_date=date(2026, 4, 15),
    )

    for item in schedule:
        assert isinstance(item, RepaymentScheduleItem)
        assert item.total_due == round(
            item.principal_due + item.interest_due,
            2,
        )


def test_monetary_values_rounded_to_two_decimals() -> None:
    schedule = generate_repayment_schedule(
        principal_amount=100_000.0,
        annual_interest_rate=7.0,
        term_months=36,
        first_payment_date=date(2026, 1, 1),
    )

    for item in schedule:
        assert item.principal_due == round(item.principal_due, 2)
        assert item.interest_due == round(item.interest_due, 2)
        assert item.total_due == round(item.total_due, 2)


def test_term_months_must_be_positive() -> None:
    with pytest.raises(ValueError, match="term_months"):
        generate_repayment_schedule(
            principal_amount=10_000.0,
            annual_interest_rate=5.0,
            term_months=0,
            first_payment_date=date(2026, 1, 1),
        )


def test_bullet_twelve_month_schedule() -> None:
    principal = 100_000.0
    monthly_interest = round(principal * 0.07 / 12, 2)
    schedule = generate_repayment_schedule(
        principal_amount=principal,
        annual_interest_rate=7.0,
        term_months=12,
        first_payment_date=date(2026, 1, 1),
        repayment_method="bullet",
    )

    assert len(schedule) == 12
    assert all(item.principal_due == 0.0 for item in schedule[:-1])
    assert schedule[-1].principal_due == principal

    for item in schedule:
        assert item.interest_due == monthly_interest
        assert item.total_due == round(item.principal_due + item.interest_due, 2)

    assert schedule[-1].total_due == round(principal + monthly_interest, 2)


def test_bullet_zero_interest() -> None:
    principal = 50_000.0
    schedule = generate_repayment_schedule(
        principal_amount=principal,
        annual_interest_rate=0.0,
        term_months=6,
        first_payment_date=date(2026, 3, 1),
        repayment_method="bullet",
    )

    assert len(schedule) == 6
    assert all(item.interest_due == 0.0 for item in schedule)
    assert all(item.principal_due == 0.0 for item in schedule[:-1])
    assert schedule[-1].principal_due == principal
    assert schedule[-1].total_due == principal


def test_bullet_invalid_term_months() -> None:
    with pytest.raises(ValueError, match="term_months"):
        generate_repayment_schedule(
            principal_amount=10_000.0,
            annual_interest_rate=7.0,
            term_months=0,
            first_payment_date=date(2026, 1, 1),
            repayment_method="bullet",
        )


def test_unsupported_repayment_method_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported repayment_method"):
        generate_repayment_schedule(
            principal_amount=10_000.0,
            annual_interest_rate=7.0,
            term_months=12,
            first_payment_date=date(2026, 1, 1),
            repayment_method="interest_only",
        )
