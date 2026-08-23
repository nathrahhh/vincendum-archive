"""Unit tests for OpenBankingService (TrueLayerClient mocked; no live HTTP)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.integrations.truelayer_client import (
    BankAccount,
    BankTransaction,
    DataConnection,
    TransactionsRequestResult,
    TrueLayerAPIError,
)
from app.services.open_banking_service import OpenBankingService


@pytest.fixture()
def client() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(client: MagicMock) -> OpenBankingService:
    return OpenBankingService(client)


def test_start_connection_delegates_to_create_connection(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.create_connection.return_value = DataConnection(
        id="conn-1",
        status="authorization_required",
        user_id="user-1",
        hosted_page_uri="https://app.truelayer.com/data/conn-1",
    )

    result = service.start_connection(
        user_name="Jane Smith",
        user_email="jane@example.com",
        return_uri="https://example.com/open-banking/callback",
        user_ip="203.0.113.10",
    )

    client.create_connection.assert_called_once()
    payload = client.create_connection.call_args.args[0]
    kwargs = client.create_connection.call_args.kwargs
    assert kwargs["user_ip"] == "203.0.113.10"
    assert payload["scopes"] == ["accounts", "transactions"]
    assert payload["provider_selection"]["type"] == "user_selected"
    assert payload["provider_selection"]["filter"]["countries"] == ["GB"]
    assert payload["user"] == {
        "name": "Jane Smith",
        "email": "jane@example.com",
    }
    assert payload["hosted_page"]["return_uri"] == (
        "https://example.com/open-banking/callback"
    )
    assert result.id == "conn-1"
    assert result.status == "authorization_required"
    assert result.hosted_page_uri is not None
    assert result.user_id == "user-1"


def test_start_connection_uses_accounts_and_transactions_scopes(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.create_connection.return_value = DataConnection(
        id="conn-2",
        status="authorization_required",
    )

    service.start_connection(
        user_name="Jane",
        user_email="jane@example.com",
        return_uri="https://example.com/callback",
    )

    payload = client.create_connection.call_args.args[0]
    assert payload["scopes"] == ["accounts", "transactions"]


def test_list_accounts_delegates(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.list_connected_accounts.return_value = [
        BankAccount(id="acc-1", type="account", currency="GBP"),
    ]

    accounts = service.list_accounts("conn-1", user_ip="198.51.100.1")

    client.list_connected_accounts.assert_called_once_with(
        "conn-1",
        user_ip="198.51.100.1",
        account_type=None,
        cursor=None,
    )
    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"


def test_create_transaction_request_delegates(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.create_transactions_request.return_value = TransactionsRequestResult(
        id="req-1",
        status="pending",
    )

    result = service.create_transaction_request(
        "conn-1",
        "acc-1",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 1, 31),
        user_ip="203.0.113.5",
    )

    client.create_transactions_request.assert_called_once_with(
        "conn-1",
        "acc-1",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 1, 31),
        cursor=None,
        page_size=None,
        enrichment=None,
        user_ip="203.0.113.5",
    )
    assert result.id == "req-1"
    assert result.status == "pending"


def test_get_transaction_request_delegates(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.get_transactions_request.return_value = TransactionsRequestResult(
        id="req-1",
        status="completed",
        items=(),
    )

    result = service.get_transaction_request(
        "conn-1",
        "acc-1",
        "req-1",
        user_ip="203.0.113.5",
    )

    client.get_transactions_request.assert_called_once_with(
        "conn-1",
        "acc-1",
        "req-1",
        user_ip="203.0.113.5",
    )
    assert result.status == "completed"


def test_finalize_connection_authorization_success(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.list_connected_accounts.return_value = []

    result = service.finalize_connection_authorization(
        "conn-1",
        user_ip="203.0.113.10",
    )

    client.list_connected_accounts.assert_called_once_with(
        "conn-1",
        user_ip="203.0.113.10",
    )
    assert result.authorized is True
    assert result.status == "authorized"


def test_finalize_connection_authorization_provider_denied(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.list_connected_accounts.side_effect = TrueLayerAPIError(
        "forbidden",
        status_code=403,
    )

    result = service.finalize_connection_authorization("conn-1")

    assert result.authorized is False
    assert result.status == "failed"


def test_finalize_connection_authorization_propagates_other_errors(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.list_connected_accounts.side_effect = TrueLayerAPIError(
        "upstream",
        status_code=500,
    )

    with pytest.raises(TrueLayerAPIError) as exc_info:
        service.finalize_connection_authorization("conn-1")

    assert exc_info.value.status_code == 500


def test_fetch_account_transactions_polls_until_completed(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.create_transactions_request.return_value = TransactionsRequestResult(
        id="req-1",
        status="pending",
    )
    client.get_transactions_request.return_value = TransactionsRequestResult(
        id="req-1",
        status="completed",
        items=(
            BankTransaction(
                id="txn-1",
                timestamp="2026-01-15T10:00:00Z",
                description="Salary",
                currency="GBP",
                amount_in_minor=12345,
                status="booked",
            ),
        ),
    )

    result = service.fetch_account_transactions(
        "conn-1",
        "acc-1",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 1, 31),
        poll_interval_seconds=0,
        max_poll_attempts=5,
    )

    assert len(result) == 1
    assert result[0].truelayer_transaction_id == "txn-1"
    assert result[0].amount == Decimal("123.45")
    assert result[0].transaction_type == "booked"
    assert result[0].booking_date is not None
    assert result[0].value_date is None
    client.create_transactions_request.assert_called_once()
    client.get_transactions_request.assert_called()


def test_fetch_account_transactions_follows_pagination(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.create_transactions_request.side_effect = [
        TransactionsRequestResult(
            id="req-1",
            status="completed",
            items=(
                BankTransaction(
                    id="txn-1",
                    timestamp="2026-01-01T00:00:00Z",
                    description="A",
                    currency="GBP",
                    amount_in_minor=100,
                    status="booked",
                ),
            ),
            next_cursor="cursor-2",
        ),
        TransactionsRequestResult(
            id="req-2",
            status="completed",
            items=(
                BankTransaction(
                    id="txn-2",
                    timestamp="2026-01-02T00:00:00Z",
                    description="B",
                    currency="GBP",
                    amount_in_minor=200,
                    status="booked",
                ),
            ),
            next_cursor=None,
        ),
    ]

    result = service.fetch_account_transactions(
        "conn-1",
        "acc-1",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 1, 31),
        poll_interval_seconds=0,
    )

    assert [item.truelayer_transaction_id for item in result] == ["txn-1", "txn-2"]
    assert client.create_transactions_request.call_count == 2
    second_kwargs = client.create_transactions_request.call_args_list[1].kwargs
    assert second_kwargs["cursor"] == "cursor-2"


def test_default_transaction_date_range_uses_env(
    service: OpenBankingService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_BANKING_INITIAL_TRANSACTION_HISTORY_DAYS", "30")
    start, end = service.default_transaction_date_range(as_of=date(2026, 2, 1))
    assert end == date(2026, 2, 1)
    assert start == date(2026, 1, 2)


def test_invalid_date_range_rejected(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    with pytest.raises(ValueError, match="from_date"):
        service.create_transaction_request(
            "conn-1",
            "acc-1",
            from_date=date(2026, 2, 1),
            to_date=date(2026, 1, 1),
        )

    client.create_transactions_request.assert_not_called()


def test_truelayer_exceptions_propagate(
    service: OpenBankingService,
    client: MagicMock,
) -> None:
    client.list_connected_accounts.side_effect = TrueLayerAPIError(
        "Connection not authorised",
        status_code=403,
        trace_id="trace-1",
    )

    with pytest.raises(TrueLayerAPIError) as exc_info:
        service.list_accounts("conn-1")

    assert exc_info.value.status_code == 403
    assert exc_info.value.trace_id == "trace-1"
