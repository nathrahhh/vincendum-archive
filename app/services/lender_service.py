"""Lender capital-base business rules."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM


def get_lender_for_user(db: Session, lender_id: int) -> LenderORM:
    """Return the lender for ``lender_id`` or raise if it does not exist."""
    lender = db.get(LenderORM, lender_id)
    if lender is None:
        raise ValueError(f"Lender {lender_id} not found")
    return lender


def get_lender_capital_base(db: Session, lender_id: int) -> float:
    """Return ``capital_base`` for ``lender_id``."""
    lender = get_lender_for_user(db, lender_id)
    return float(lender.capital_base)


def _total_portfolio_allocation(
    db: Session,
    lender_id: int,
    *,
    exclude_portfolio_id: int | None = None,
) -> float:
    """Sum ``capital_allocation`` for portfolios owned by ``lender_id``."""
    query = select(
        func.coalesce(func.sum(PortfolioORM.capital_allocation), 0.0),
    ).where(PortfolioORM.lender_id == lender_id)
    if exclude_portfolio_id is not None:
        query = query.where(PortfolioORM.id != exclude_portfolio_id)
    return float(db.execute(query).scalar_one())


def validate_portfolio_capital_allocation(
    db: Session,
    lender_id: int,
    proposed_allocation: float,
    exclude_portfolio_id: int | None = None,
) -> None:
    """
    Ensure ``proposed_allocation`` fits within the lender's remaining capital.

    When updating an existing portfolio, pass ``exclude_portfolio_id`` so its
    current allocation is not double-counted against the ceiling.
    """
    if proposed_allocation < 0:
        raise HTTPException(
            status_code=400,
            detail="Capital allocation cannot be negative",
        )

    lender = get_lender_for_user(db, lender_id)
    existing_allocation = _total_portfolio_allocation(
        db,
        lender_id,
        exclude_portfolio_id=exclude_portfolio_id,
    )
    total_allocation = existing_allocation + proposed_allocation
    capital_base = float(lender.capital_base)

    if total_allocation > capital_base:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total portfolio capital allocation ({total_allocation:,.2f}) "
                f"would exceed lender capital base ({capital_base:,.2f})"
            ),
        )


def validate_lender_capital_base(
    db: Session,
    lender_id: int,
    proposed_capital_base: float,
) -> None:
    """
    Ensure a lender's capital base can cover existing portfolio allocations.

    Rejects non-positive values and updates that would leave allocated capital
    above the proposed ceiling.
    """
    if proposed_capital_base <= 0:
        raise HTTPException(
            status_code=400,
            detail="Capital base must be greater than zero",
        )

    get_lender_for_user(db, lender_id)
    total_allocation = _total_portfolio_allocation(db, lender_id)

    if total_allocation > proposed_capital_base:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Capital base ({proposed_capital_base:,.2f}) cannot be lower "
                f"than total portfolio allocations ({total_allocation:,.2f})"
            ),
        )


def update_lender_capital_base(
    db: Session,
    lender_id: int,
    proposed_capital_base: float,
) -> LenderORM:
    """Validate and persist a new capital base for ``lender_id``."""
    validate_lender_capital_base(db, lender_id, proposed_capital_base)
    lender = get_lender_for_user(db, lender_id)
    lender.capital_base = proposed_capital_base
    db.commit()
    db.refresh(lender)
    return lender
