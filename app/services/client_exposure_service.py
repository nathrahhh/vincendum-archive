from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.position import PositionORM


def get_client_exposure(db: Session, client_id: int) -> dict:
    client = db.get(ClientORM, client_id)

    if client is None:
        raise ValueError(f"Client {client_id} not found")

    positions = db.execute(
        select(PositionORM).where(
            PositionORM.client_id == client_id,
        )
    ).scalars().all()

    current_exposure = sum(position.value for position in positions)

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
        "deal_count": len(positions),
        "deals": [
            {
                "id": position.id,
                "name": position.name,
                "value": position.value,
                "industry": position.industry,
                "status": "APPROVED",
            }
            for position in positions
        ],
    }