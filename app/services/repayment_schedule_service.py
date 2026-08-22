"""Generate fixed-rate monthly repayment schedules from deal terms.

Pure calculation only — no database, SQLAlchemy, FastAPI, or ORM usage.

Supported configurations:
- repayment_method = amortizing | bullet
- interest_rate_type = fixed (caller responsibility)
- payment_frequency = monthly
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

_SUPPORTED_REPAYMENT_METHODS = frozenset({"amortizing", "bullet"})


@dataclass(frozen=True)
class RepaymentScheduleItem:
    due_date: date
    principal_due: float
    interest_due: float
    total_due: float


def _round_money(value: float) -> float:
    return round(value, 2)


def _add_months(start: date, months: int) -> date:
    """Return ``start`` advanced by ``months``, clamping the day to the month."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(start.day, last_day)
    return date(year, month, day)


def _fixed_monthly_payment(
    principal_amount: float,
    monthly_rate: float,
    term_months: int,
) -> float:
    if monthly_rate == 0:
        return principal_amount / term_months

    factor = (1 + monthly_rate) ** term_months
    return principal_amount * monthly_rate * factor / (factor - 1)


def _generate_amortizing_schedule(
    principal_amount: float,
    annual_interest_rate: float,
    term_months: int,
    first_payment_date: date,
) -> list[RepaymentScheduleItem]:
    monthly_rate = annual_interest_rate / 100 / 12
    payment = _fixed_monthly_payment(
        principal_amount,
        monthly_rate,
        term_months,
    )

    remaining_principal = _round_money(principal_amount)
    schedule: list[RepaymentScheduleItem] = []

    for month_index in range(term_months):
        due_date = _add_months(first_payment_date, month_index)
        is_final = month_index == term_months - 1

        interest_due = _round_money(remaining_principal * monthly_rate)

        if is_final:
            principal_due = remaining_principal
        else:
            principal_due = _round_money(payment - interest_due)
            if principal_due > remaining_principal:
                principal_due = remaining_principal

        principal_due = _round_money(principal_due)
        interest_due = _round_money(interest_due)
        total_due = _round_money(principal_due + interest_due)

        schedule.append(
            RepaymentScheduleItem(
                due_date=due_date,
                principal_due=principal_due,
                interest_due=interest_due,
                total_due=total_due,
            )
        )

        remaining_principal = _round_money(remaining_principal - principal_due)

    return schedule


def _generate_bullet_schedule(
    principal_amount: float,
    annual_interest_rate: float,
    term_months: int,
    first_payment_date: date,
) -> list[RepaymentScheduleItem]:
    """Interest-only monthly payments with principal repaid on the final instalment."""
    monthly_rate = annual_interest_rate / 100 / 12
    remaining_principal = _round_money(principal_amount)
    schedule: list[RepaymentScheduleItem] = []

    for month_index in range(term_months):
        due_date = _add_months(first_payment_date, month_index)
        is_final = month_index == term_months - 1

        interest_due = _round_money(remaining_principal * monthly_rate)
        principal_due = remaining_principal if is_final else 0.0
        principal_due = _round_money(principal_due)
        total_due = _round_money(principal_due + interest_due)

        schedule.append(
            RepaymentScheduleItem(
                due_date=due_date,
                principal_due=principal_due,
                interest_due=interest_due,
                total_due=total_due,
            )
        )

        remaining_principal = _round_money(remaining_principal - principal_due)

    return schedule


def generate_repayment_schedule(
    principal_amount: float,
    annual_interest_rate: float,
    term_months: int,
    first_payment_date: date,
    repayment_method: str = "amortizing",
) -> list[RepaymentScheduleItem]:
    """Build a fixed-rate monthly schedule for the given repayment method.

    ``annual_interest_rate`` is a percentage (e.g. ``7.0`` means 7% per year).
    Returns exactly ``term_months`` items.

    Supported ``repayment_method`` values: ``amortizing``, ``bullet``.
    """
    if term_months <= 0:
        raise ValueError("term_months must be a positive integer")

    if repayment_method not in _SUPPORTED_REPAYMENT_METHODS:
        raise ValueError(
            f"Unsupported repayment_method={repayment_method!r}; "
            f"supported: {sorted(_SUPPORTED_REPAYMENT_METHODS)}"
        )

    if repayment_method == "bullet":
        return _generate_bullet_schedule(
            principal_amount=principal_amount,
            annual_interest_rate=annual_interest_rate,
            term_months=term_months,
            first_payment_date=first_payment_date,
        )

    return _generate_amortizing_schedule(
        principal_amount=principal_amount,
        annual_interest_rate=annual_interest_rate,
        term_months=term_months,
        first_payment_date=first_payment_date,
    )
