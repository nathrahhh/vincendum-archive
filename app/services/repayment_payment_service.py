"""Record actual payments against scheduled RepaymentORM rows.

Architecture:
- repayment_schedule_service: pure calculation of what should be paid
- repayment_service: create/persist contractual schedule
- repayment_payment_service: record amounts received against instalments

Supported statuses for this layer:
    SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE

OVERDUE is reserved for a later detection pass; record_payment only transitions
to PARTIALLY_PAID or PAID.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repayment import RepaymentORM

_MONEY_QUANT = Decimal("0.01")


def _to_money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


def _as_float(value: Decimal) -> float:
    return float(value)


def _get_repayment_or_404(db: Session, repayment_id: int) -> RepaymentORM:
    repayment = db.execute(
        select(RepaymentORM).where(RepaymentORM.id == repayment_id)
    ).scalar_one_or_none()
    if repayment is None:
        raise HTTPException(
            status_code=404,
            detail=f"Repayment {repayment_id} not found",
        )
    return repayment


def record_payment(
    db: Session,
    repayment_id: int,
    amount: float,
    *,
    paid_at: date | None = None,
) -> RepaymentORM:
    """Apply a payment to a scheduled instalment (interest first, then principal)."""
    repayment = _get_repayment_or_404(db, repayment_id)

    payment = _to_money(amount)
    if payment <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero",
        )

    total_due = _to_money(repayment.total_due)
    total_paid = _to_money(repayment.total_paid)
    interest_due = _to_money(repayment.interest_due)
    interest_paid = _to_money(repayment.interest_paid)
    principal_due = _to_money(repayment.principal_due)
    principal_paid = _to_money(repayment.principal_paid)

    if total_paid >= total_due:
        raise HTTPException(
            status_code=400,
            detail=f"Repayment {repayment_id} is already fully paid",
        )

    outstanding = total_due - total_paid
    if payment > outstanding:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount {payment} exceeds outstanding balance "
                f"{outstanding} for repayment {repayment_id}"
            ),
        )

    interest_remaining = interest_due - interest_paid
    interest_apply = min(payment, interest_remaining)
    principal_apply = payment - interest_apply

    principal_remaining = principal_due - principal_paid
    if principal_apply > principal_remaining:
        # Should not happen when total_due == principal_due + interest_due,
        # but guard against inconsistent rows.
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount {payment} exceeds outstanding balance "
                f"{outstanding} for repayment {repayment_id}"
            ),
        )

    new_interest_paid = interest_paid + interest_apply
    new_principal_paid = principal_paid + principal_apply
    new_total_paid = total_paid + payment

    repayment.interest_paid = _as_float(new_interest_paid)
    repayment.principal_paid = _as_float(new_principal_paid)
    repayment.total_paid = _as_float(new_total_paid)

    if new_total_paid == total_due:
        repayment.status = "PAID"
        repayment.paid_at = paid_at if paid_at is not None else date.today()
    else:
        repayment.status = "PARTIALLY_PAID"
        repayment.paid_at = None

    db.commit()
    db.refresh(repayment)
    return repayment
