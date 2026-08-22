"""Persist calculated repayment schedules as RepaymentORM rows.

Bridges ``repayment_schedule_service.generate_repayment_schedule`` (pure calc)
and the database. Does not generate schedules automatically elsewhere.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.deal import DealORM
from app.models.repayment import RepaymentORM
from app.services.repayment_schedule_service import generate_repayment_schedule

_REQUIRED_TERM_ATTRS = (
    "principal_amount",
    "interest_rate",
    "term_months",
    "first_payment_date",
    "interest_rate_type",
    "repayment_method",
    "payment_frequency",
)

_SUPPORTED_INTEREST_RATE_TYPE = "fixed"
_SUPPORTED_REPAYMENT_METHODS = frozenset({"amortizing", "bullet"})
_SUPPORTED_PAYMENT_FREQUENCY = "monthly"


def _get_deal_or_404(db: Session, deal_id: int) -> DealORM:
    deal = db.execute(
        select(DealORM).where(DealORM.id == deal_id)
    ).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return deal


def _validate_required_terms(deal: DealORM) -> None:
    missing = [
        name
        for name in _REQUIRED_TERM_ATTRS
        if getattr(deal, name) is None
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Deal {deal.id} is missing required repayment terms: "
                f"{', '.join(missing)}"
            ),
        )


def _validate_supported_configuration(deal: DealORM) -> None:
    unsupported: list[str] = []
    if deal.interest_rate_type != _SUPPORTED_INTEREST_RATE_TYPE:
        unsupported.append(
            f"interest_rate_type={deal.interest_rate_type!r} "
            f"(supported: {_SUPPORTED_INTEREST_RATE_TYPE!r})"
        )
    if deal.repayment_method not in _SUPPORTED_REPAYMENT_METHODS:
        unsupported.append(
            f"repayment_method={deal.repayment_method!r} "
            f"(supported: {sorted(_SUPPORTED_REPAYMENT_METHODS)!r})"
        )
    if deal.payment_frequency != _SUPPORTED_PAYMENT_FREQUENCY:
        unsupported.append(
            f"payment_frequency={deal.payment_frequency!r} "
            f"(supported: {_SUPPORTED_PAYMENT_FREQUENCY!r})"
        )
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Deal {deal.id} repayment configuration is not currently "
                f"supported: {'; '.join(unsupported)}"
            ),
        )


def _ensure_no_existing_schedule(db: Session, deal_id: int) -> None:
    already_exists = db.execute(
        select(exists().where(RepaymentORM.deal_id == deal_id))
    ).scalar()
    if already_exists:
        raise HTTPException(
            status_code=409,
            detail=f"A repayment schedule already exists for deal {deal_id}",
        )


def generate_and_store_schedule(
    db: Session,
    deal_id: int,
    *,
    commit: bool = True,
) -> list[RepaymentORM]:
    """Calculate a repayment schedule for ``deal_id`` and persist RepaymentORM rows.

    Supports fixed-rate monthly ``amortizing`` and ``bullet`` methods.
    When ``commit`` is False, rows are flushed onto ``db`` only so the caller can
    include them in a larger transaction (e.g. deal approval).
    """
    deal = _get_deal_or_404(db, deal_id)
    _validate_required_terms(deal)
    _validate_supported_configuration(deal)
    _ensure_no_existing_schedule(db, deal_id)

    # Validated non-None above; narrow for the type checker / call site.
    assert deal.principal_amount is not None
    assert deal.interest_rate is not None
    assert deal.term_months is not None
    assert deal.first_payment_date is not None
    assert deal.repayment_method is not None

    schedule_items = generate_repayment_schedule(
        principal_amount=deal.principal_amount,
        annual_interest_rate=deal.interest_rate,
        term_months=deal.term_months,
        first_payment_date=deal.first_payment_date,
        repayment_method=deal.repayment_method,
    )

    repayments = [
        RepaymentORM(
            deal_id=deal.id,
            due_date=item.due_date,
            principal_due=item.principal_due,
            interest_due=item.interest_due,
            total_due=item.total_due,
            principal_paid=0,
            interest_paid=0,
            total_paid=0,
            status="SCHEDULED",
            paid_at=None,
        )
        for item in schedule_items
    ]

    db.add_all(repayments)
    if commit:
        db.commit()
    else:
        db.flush()
    for repayment in repayments:
        db.refresh(repayment)
    return repayments
