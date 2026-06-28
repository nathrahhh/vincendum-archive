from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.breach import BreachORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealRecord, DealRequest, Position, RiskEvaluation
from app.services.breach_helpers import industry_for_new_breach, reason_for_new_breach
from app.services.deal_service import approve_deal as approve_deal_service
from app.services.deal_service import reject_deal as reject_deal_service
from app.services.concentration_risk_engine import RiskEngine

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=list[DealRecord])
def list_deals(db: Session = Depends(get_db)) -> list[DealRecord]:
    """Return historical evaluated deals, newest first."""
    rows = db.execute(select(DealORM).order_by(DealORM.id.desc())).scalars().all()
    return [
        DealRecord(
            id=row.id,
            name=row.name,
            value=row.value,
            industry=row.industry,
            status=row.status,
        )
        for row in rows
    ]


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

    # RiskEngine gatekeeper: auto-reject fails risk checks; pass cases await admin approval.
    deal_status = "REJECTED" if result.status.value == "REJECTED" else "PENDING"
    logged_deal = DealORM(
        name=deal.name,
        value=deal.value,
        industry=deal.industry,
        status=deal_status,
    )
    db.add(logged_deal)
    db.commit()
    db.refresh(logged_deal)

    if result.breaches:
        # Breaches are stored separately to preserve a normalized risk-event log.
        for breach in result.breaches:
            breach_row = BreachORM(
                reason=reason_for_new_breach(breach),
                industry=industry_for_new_breach(breach, deal.industry),
                rule=breach.rule,
                limit_pct=breach.limit_pct,
                actual_pct=breach.actual_pct,
                detail=breach.detail,
            )
            db.add(breach_row)
        db.commit()

    return result


@router.post("/{deal_id}/approve", response_model=DealRecord)
def approve_deal(deal_id: int, db: Session = Depends(get_db)) -> DealRecord:
    """Approve a pending deal and add it to the portfolio."""
    return approve_deal_service(db, deal_id)


@router.post("/{deal_id}/reject", response_model=DealRecord)
def reject_deal(deal_id: int, db: Session = Depends(get_db)) -> DealRecord:
    """Reject a pending deal without creating a position."""
    return reject_deal_service(db, deal_id)
