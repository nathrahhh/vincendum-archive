from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.position import PositionORM
from app.models.schemas import PortfolioResponse, Position
from app.models.user import UserORM
from app.services.portfolio_analytics import build_portfolio_response

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
def list_portfolio(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> PortfolioResponse:
    """
    Return portfolio positions for this lender.

    Filters via PositionORM.client_id → ClientORM.lender_id.
    Positions with a null client_id cannot be tenant-scoped and are excluded.
    """
    lender_id = get_user_lender_id(current_user)
    rows = db.execute(
        select(PositionORM)
        .join(ClientORM, PositionORM.client_id == ClientORM.id)
        .where(ClientORM.lender_id == lender_id)
        .order_by(PositionORM.name)
    ).scalars().all()
    positions = [
        Position(name=row.name, value=row.value, industry=row.industry)
        for row in rows
    ]
    return build_portfolio_response(positions)
