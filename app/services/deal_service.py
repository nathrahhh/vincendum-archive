from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealRecord


def _get_deal_or_404(db: Session, deal_id: int) -> DealORM:
    deal = db.execute(select(DealORM).where(DealORM.id == deal_id)).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return deal


def approve_deal(db: Session, deal_id: int) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    deal.status = "APPROVED"
    position = PositionORM(name=deal.name, value=deal.value, industry=deal.industry)
    db.add(position)
    db.commit()
    db.refresh(deal)

    return DealRecord(
        id=deal.id,
        name=deal.name,
        value=deal.value,
        industry=deal.industry,
        status=deal.status,
    )


def reject_deal(db: Session, deal_id: int) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    deal.status = "REJECTED"
    db.commit()
    db.refresh(deal)

    return DealRecord(
        id=deal.id,
        name=deal.name,
        value=deal.value,
        industry=deal.industry,
        status=deal.status,
    )
