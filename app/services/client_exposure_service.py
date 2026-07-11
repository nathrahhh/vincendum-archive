from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM


def get_client_exposure(db: Session, client_id: int) -> dict:
    client = db.get(ClientORM, client_id)

    if client is None:
        raise ValueError(f"Client {client_id} not found")

    deals = db.execute(
        select(DealORM).where(
            DealORM.client_id == client_id,
            DealORM.status == "APPROVED",
        )
    ).scalars().all()

    current_exposure = sum(deal.value for deal in deals)

    remaining_credit = client.credit_limit - current_exposure

    utilization_pct = (
        current_exposure / client.credit_limit * 100
        if client.credit_limit > 0
        else 0
    )

    return {
        "credit_limit": client.credit_limit,
        "current_exposure": current_exposure,
        "remaining_credit": remaining_credit,
        "utilization_pct": round(utilization_pct, 2),
        "deal_count": len(deals),
        "deals": [
            {
                "id": deal.id,
                "name": deal.name,
                "value": deal.value,
                "industry": deal.industry,
                "status": deal.status,
            }
            for deal in deals
        ],
    }