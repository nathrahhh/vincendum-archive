from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.schemas import PortfolioCreateRequest, PortfolioRecord
from app.models.user import UserORM
from app.services.portfolio_service import (
    PortfolioSummary,
    create_portfolio,
    get_portfolio_for_lender,
    get_portfolio_summary,
    get_portfolios_for_lender,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("", response_model=PortfolioRecord)
def create_portfolio_route(
    payload: PortfolioCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> PortfolioRecord:
    """Create a portfolio for the authenticated lender."""
    lender_id = get_user_lender_id(current_user)
    return create_portfolio(
        db,
        lender_id=lender_id,
        name=payload.name,
        capital_allocation=payload.capital_allocation,
    )


@router.get("", response_model=list[PortfolioRecord])
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> list[PortfolioRecord]:
    """Return all portfolios owned by the authenticated lender."""
    lender_id = get_user_lender_id(current_user)
    return get_portfolios_for_lender(db, lender_id)


@router.get("/{portfolio_id}")
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> PortfolioSummary:
    """Return portfolio monitoring metrics for an owned portfolio."""
    lender_id = get_user_lender_id(current_user)
    if get_portfolio_for_lender(db, portfolio_id, lender_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Portfolio {portfolio_id} not found",
        )
    return get_portfolio_summary(db, portfolio_id)
