from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import PortfolioResponse
from app.services.portfolio_analytics import build_portfolio_response
from app.services.portfolio_store import get_portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
def list_portfolio(db: Session = Depends(get_db)) -> PortfolioResponse:
    """Return portfolio positions with analytics from PostgreSQL."""
    positions = get_portfolio(db)
    return build_portfolio_response(positions)
