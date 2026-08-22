"""Unit tests for OpenBankingService (TrueLayerClient mocked; no live HTTP)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.integrations.truelayer_client import (
    BankAccount,
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
