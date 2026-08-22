"""Vincendum-facing Open Banking operations.

Wraps ``TrueLayerClient`` without performing HTTP itself. Does not persist
bank data, match repayments, or expose credentials/tokens.
"""

from __future__ import annotations

from datetime import date

from app.integrations.truelayer_client import (
    BankAccount,
    DataConnection,
    TransactionsRequestResult,
    TrueLayerClient,
)

_DEFAULT_SCOPES = ("accounts", "transactions")


class OpenBankingService:
    """Business-level Open Banking operations backed by TrueLayer Data API v3."""

    def __init__(self, client: TrueLayerClient) -> None:
        self.client = client

    def start_connection(
        self,
        *,
        user_name: str,
        user_email: str,
        return_uri: str,
        scopes: tuple[str, ...] | list[str] = _DEFAULT_SCOPES,
        user_ip: str | None = None,
        user_agent: str | None = None,
        data_access_type: str = "recurring",
    ) -> DataConnection:
        """Create a Data V3 connection and return the hosted authorisation URI."""
        name = user_name.strip()
        email = user_email.strip()
        redirect = return_uri.strip()
        if not name:
            raise ValueError("user_name is required")
        if not email:
            raise ValueError("user_email is required")
        if not redirect:
            raise ValueError("return_uri is required")

        requested_scopes = [scope.strip() for scope in scopes if scope.strip()]
        if not requested_scopes:
            raise ValueError("scopes must not be empty")

        payload = {
            "scopes": requested_scopes,
            "provider_selection": {
                "type": "user_selected",
                "filter": {
                    "countries": ["GB"],
                },
            },
            "user": {
                "name": name,
                "email": email,
            },
            "user_consent": {
                "type": "authorization_flow_captured",
            },
            "hosted_page": {
                "type": "authorization_flow",
                "return_uri": redirect,
            },
            "data_access_type": data_access_type,
        }
        return self.client.create_connection(
            payload,
            user_ip=user_ip,
            user_agent=user_agent,
        )

    def list_accounts(
        self,
        connection_id: str,
        *,
        user_ip: str | None = None,
        account_type: str | None = None,
        cursor: str | None = None,
    ) -> list[BankAccount]:
        """List bank accounts for an authorised connection."""
        connection_id = _require_non_empty(connection_id, "connection_id")
        return self.client.list_connected_accounts(
            connection_id,
            user_ip=user_ip,
            account_type=account_type,
            cursor=cursor,
        )

    def create_transaction_request(
        self,
        connection_id: str,
        account_id: str,
        *,
        from_date: date,
        to_date: date,
        cursor: str | None = None,
        page_size: int | None = None,
        enrichment: dict | None = None,
        user_ip: str | None = None,
    ) -> TransactionsRequestResult:
        """Start an async transaction retrieval request (does not poll)."""
        connection_id = _require_non_empty(connection_id, "connection_id")
        account_id = _require_non_empty(account_id, "account_id")
        _validate_date_range(from_date, to_date)
        return self.client.create_transactions_request(
            connection_id,
            account_id,
            from_date=from_date,
            to_date=to_date,
            cursor=cursor,
            page_size=page_size,
            enrichment=enrichment,
            user_ip=user_ip,
        )

    def get_transaction_request(
        self,
        connection_id: str,
        account_id: str,
        request_id: str,
        *,
        user_ip: str | None = None,
    ) -> TransactionsRequestResult:
        """Fetch the status/result of a previously created transactions request."""
        connection_id = _require_non_empty(connection_id, "connection_id")
        account_id = _require_non_empty(account_id, "account_id")
        request_id = _require_non_empty(request_id, "request_id")
        return self.client.get_transactions_request(
            connection_id,
            account_id,
            request_id,
            user_ip=user_ip,
        )


def _require_non_empty(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def _validate_date_range(from_date: date, to_date: date) -> None:
    if from_date > to_date:
        raise ValueError("from_date must be on or before to_date")
