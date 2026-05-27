from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import DealRequest, RiskEvaluation
from app.services.portfolio_store import get_portfolio
from app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/deals", tags=["deals"])
risk_engine = RiskEngine()


@router.post("/evaluate", response_model=RiskEvaluation)
def evaluate_deal(
    deal: DealRequest,
    db: Session = Depends(get_db),
) -> RiskEvaluation:
    """
    Simulate adding a proposed deal to the portfolio and run
    pre-trade concentration risk checks.
    """
    portfolio = get_portfolio(db)
    return risk_engine.evaluate_deal(portfolio, deal)
