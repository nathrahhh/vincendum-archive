from app.services.client_exposure_service import get_client_exposure


class ClientCreditEngine:

    def evaluate_deal(self, db, client_id: int, deal_value: float) -> dict:

        exposure = get_client_exposure(db, client_id)

        remaining_credit = exposure["remaining_credit"]

        approved = deal_value <= remaining_credit

        return {
            "approved": approved,
            "credit_limit": exposure["credit_limit"],
            "current_exposure": exposure["current_exposure"],
            "remaining_credit": remaining_credit,
            "requested_amount": deal_value,
            "reason": None if approved else "CLIENT_CREDIT_LIMIT_EXCEEDED",
        }