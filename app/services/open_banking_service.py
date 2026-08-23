"""Vincendum-facing Open Banking operations.

Wraps ``TrueLayerClient`` without performing HTTP itself. Does not persist
bank data, match repayments, or expose credentials/tokens.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.integrations.truelayer_client import (
    BankAccount,
    BankTransaction,
    DataConnection,
    TransactionsRequestResult,
    TrueLayerAPIError,
    TrueLayerClient,
    TrueLayerError,
)

_DEFAULT_SCOPES = ("accounts", "transactions")
_DEFAULT_INITIAL_HISTORY_DAYS = 90
_DEFAULT_POLL_INTERVAL_SECONDS = 0.5
_DEFAULT_MAX_POLL_ATTEMPTS = 40

# Terminal / lifecycle statuses persisted on BankConnectionORM.
STATUS_AUTHORIZATION_REQUIRED = "authorization_required"
STATUS_AUTHORIZED = "authorized"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConnectionAuthorizationResult:
    """Outcome of confirming whether a TrueLayer connection is usable."""

    status: str
    authorized: bool


@dataclass(frozen=True)
class SyncedTransaction:
    """Persistence-friendly transaction mapped from TrueLayer Data V3."""

    truelayer_transaction_id: str
    booking_date: datetime | None
    value_date: datetime | None
    amount: Decimal
    currency: str
    description: str | None
    transaction_type: str | None


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

    def finalize_connection_authorization(
        self,
        connection_id: str,
        *,
        user_ip: str | None = None,
    ) -> ConnectionAuthorizationResult:
        """Confirm whether a connection can access accounts (authoritative check).

        TrueLayer Data V3 does not document return_uri query parameters that
        report success/failure. The hosted return only indicates the UI flow
        finished. We treat successful ``list_connected_accounts`` as evidence
        the connection is authorised; provider 401/403 means it is not.
        """
        connection_id = _require_non_empty(connection_id, "connection_id")
        try:
            self.client.list_connected_accounts(
                connection_id,
                user_ip=user_ip,
            )
        except TrueLayerAPIError as exc:
            if exc.status_code in {401, 403}:
                return ConnectionAuthorizationResult(
                    status=STATUS_FAILED,
                    authorized=False,
                )
            raise

        return ConnectionAuthorizationResult(
            status=STATUS_AUTHORIZED,
            authorized=True,
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

    def initial_transaction_history_days(self) -> int:
        """Configurable lookback window for the first transaction sync."""
        raw = os.getenv("OPEN_BANKING_INITIAL_TRANSACTION_HISTORY_DAYS", "").strip()
        if not raw:
            return _DEFAULT_INITIAL_HISTORY_DAYS
        try:
            days = int(raw)
        except ValueError as exc:
            raise ValueError(
                "OPEN_BANKING_INITIAL_TRANSACTION_HISTORY_DAYS must be an integer"
            ) from exc
        if days < 1:
            raise ValueError(
                "OPEN_BANKING_INITIAL_TRANSACTION_HISTORY_DAYS must be >= 1"
            )
        return days

    def default_transaction_date_range(
        self,
        *,
        as_of: date | None = None,
    ) -> tuple[date, date]:
        """Return (from_date, to_date) for an initial historical sync."""
        end = as_of or datetime.now(timezone.utc).date()
        start = end - timedelta(days=self.initial_transaction_history_days())
        return start, end

    def fetch_account_transactions(
        self,
        connection_id: str,
        account_id: str,
        *,
        from_date: date,
        to_date: date,
        user_ip: str | None = None,
        poll_interval_seconds: float | None = None,
        max_poll_attempts: int | None = None,
    ) -> list[SyncedTransaction]:
        """Create/poll TrueLayer transaction requests and return mapped items.

        Follows the async create → get flow, including pagination via
        ``next_cursor``. Does not persist rows.
        """
        connection_id = _require_non_empty(connection_id, "connection_id")
        account_id = _require_non_empty(account_id, "account_id")
        _validate_date_range(from_date, to_date)

        interval = (
            _DEFAULT_POLL_INTERVAL_SECONDS
            if poll_interval_seconds is None
            else poll_interval_seconds
        )
        attempts = (
            _DEFAULT_MAX_POLL_ATTEMPTS
            if max_poll_attempts is None
            else max_poll_attempts
        )
        if interval < 0:
            raise ValueError("poll_interval_seconds must be >= 0")
        if attempts < 1:
            raise ValueError("max_poll_attempts must be >= 1")

        synced: list[SyncedTransaction] = []
        cursor: str | None = None

        while True:
            result = self._await_transactions_request(
                connection_id,
                account_id,
                from_date=from_date,
                to_date=to_date,
                cursor=cursor,
                user_ip=user_ip,
                poll_interval_seconds=interval,
                max_poll_attempts=attempts,
            )
            for item in result.items:
                synced.append(_map_transaction(item))

            if not result.next_cursor:
                break
            cursor = result.next_cursor

        return synced

    def _await_transactions_request(
        self,
        connection_id: str,
        account_id: str,
        *,
        from_date: date,
        to_date: date,
        cursor: str | None,
        user_ip: str | None,
        poll_interval_seconds: float,
        max_poll_attempts: int,
    ) -> TransactionsRequestResult:
        created = self.client.create_transactions_request(
            connection_id,
            account_id,
            from_date=from_date,
            to_date=to_date,
            cursor=cursor,
            user_ip=user_ip,
        )
        if created.status == "completed":
            return created
        if created.status == "failed":
            raise TrueLayerError(
                "TrueLayer transaction request failed.",
            )

        result = created
        for _ in range(max_poll_attempts):
            if poll_interval_seconds:
                time.sleep(poll_interval_seconds)
            result = self.client.get_transactions_request(
                connection_id,
                account_id,
                created.id,
                user_ip=user_ip,
            )
            if result.status == "completed":
                return result
            if result.status == "failed":
                raise TrueLayerError(
                    "TrueLayer transaction request failed.",
                )

        logger.warning(
            "TrueLayer transaction request timed out request_id=%s",
            created.id,
        )
        raise TrueLayerError(
            "TrueLayer transaction request timed out.",
        )


def _map_transaction(item: BankTransaction) -> SyncedTransaction:
    return SyncedTransaction(
        truelayer_transaction_id=item.id,
        booking_date=_parse_timestamp(item.timestamp),
        value_date=None,
        amount=Decimal(item.amount_in_minor) / Decimal(100),
        currency=item.currency,
        description=item.description or None,
        transaction_type=item.status or None,
    )


def _parse_timestamp(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _require_non_empty(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def _validate_date_range(from_date: date, to_date: date) -> None:
    if from_date > to_date:
        raise ValueError("from_date must be on or before to_date")
