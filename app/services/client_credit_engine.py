from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM


class ClientCreditEngine:

    def evaluate_deal(self, db: Session, client_id: int, deal_value: float) -> dict:
        client = db.get(ClientORM, client_id)
        if client is None:
            raise ValueError(f"Client {client_id} not found")

        current_exposure = db.execute(
            select(func.coalesce(func.sum(PositionORM.value), 0.0))
            .select_from(PositionORM)
            .join(DealORM, PositionORM.deal_id == DealORM.id)
            .where(DealORM.client_id == client_id)
        ).scalar_one()
        current_exposure = float(current_exposure)

        remaining_credit = client.credit_limit - current_exposure
        approved = deal_value <= remaining_credit

        return {
            "approved": approved,
            "credit_limit": client.credit_limit,
            "current_exposure": current_exposure,
            "remaining_credit": remaining_credit,
            "requested_amount": deal_value,
            "reason": None if approved else "CLIENT_CREDIT_LIMIT_EXCEEDED",
        }
