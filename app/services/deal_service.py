from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealRecord, DealRequest


def _get_deal_or_404(db: Session, deal_id: int) -> DealORM:
    deal = db.execute(select(DealORM).where(DealORM.id == deal_id)).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return deal


def _client_industry(db: Session, client_id: int) -> str:
    client = db.execute(
        select(ClientORM).where(ClientORM.id == client_id)
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client.industry


def _to_deal_record(deal: DealORM) -> DealRecord:
    return DealRecord(
        id=deal.id,
        client_id=deal.client_id,
        name=deal.name,
        value=deal.value,
        status=deal.status,
    )


def create_deal(
    db: Session,
    *,
    current_client: ClientORM,
    payload: DealRequest,
) -> DealRecord:
    """
    Create a PENDING deal owned by ``current_client``.

    Ownership comes only from the authenticated client profile.
    """
    deal = DealORM(
        client_id=current_client.id,
        name=payload.name.strip(),
        value=payload.value,
        status="PENDING",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return _to_deal_record(deal)


def approve_deal(db: Session, deal_id: int) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    industry = _client_industry(db, deal.client_id)
    deal.status = "APPROVED"
    position = PositionORM(name=deal.name, value=deal.value, industry=industry)
    db.add(position)
    db.commit()
    db.refresh(deal)

    return _to_deal_record(deal)


def reject_deal(db: Session, deal_id: int) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    deal.status = "REJECTED"
    db.commit()
    db.refresh(deal)

    return _to_deal_record(deal)
