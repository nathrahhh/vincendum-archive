from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.breach import BreachORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealRequest, Position, RiskEvaluation
from app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/deals", tags=["deals"])
breaches_router = APIRouter(tags=["breaches"])


@router.post("/evaluate", response_model=RiskEvaluation)
def evaluate_deal(
    deal: DealRequest,
    db: Session = Depends(get_db),
) -> RiskEvaluation:
    """
    Evaluate a proposed deal using RiskEngine and persist audit records.
    """
    existing_positions = db.execute(select(PositionORM).order_by(PositionORM.name)).scalars().all()
    portfolio = [Position(name=p.name, value=p.value, industry=p.industry) for p in existing_positions]
    risk_engine = RiskEngine()
    result = risk_engine.evaluate_deal(portfolio=portfolio, deal=deal)

    # Deals table is the full audit trail of every submitted trade attempt.
    logged_deal = DealORM(
        name=deal.name,
        value=deal.value,
        industry=deal.industry,
        status=result.status.value,
    )
    db.add(logged_deal)
    db.commit()
    db.refresh(logged_deal)

    if result.breaches:
        # Breaches are stored separately to preserve a normalized risk-event log.
        for breach in result.breaches:
            breach_row = BreachORM(
                rule=breach.rule,
                limit_pct=breach.limit_pct,
                actual_pct=breach.actual_pct,
                detail=breach.detail,
            )
            db.add(breach_row)
        db.commit()

    if result.status.value == "APPROVED":
        # Only approved deals become funded positions in the live portfolio.
        position = PositionORM(name=deal.name, value=deal.value, industry=deal.industry)
        db.add(position)
        db.commit()
        db.refresh(position)

    return result


@breaches_router.get("/breaches")
def list_breaches(db: Session = Depends(get_db)) -> dict[str, list[dict[str, float | int | str]]]:
    rows = db.execute(select(BreachORM).order_by(BreachORM.id.desc())).scalars().all()
    grouped: dict[str, list[dict[str, float | int | str]]] = {}
    for breach in rows:
        grouped.setdefault(breach.industry, []).append(
            {
                "id": breach.id,
                "reason": breach.reason,
                "rule": breach.rule,
                "limit_pct": breach.limit_pct,
                "actual_pct": breach.actual_pct,
                "detail": breach.detail,
            }
        )
    return grouped
