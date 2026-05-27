from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import Position
from app.services.portfolio_store import get_portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=list[Position])
def list_portfolio(db: Session = Depends(get_db)) -> list[Position]:
    """Return the current lending portfolio from PostgreSQL."""
    return get_portfolio(db)
