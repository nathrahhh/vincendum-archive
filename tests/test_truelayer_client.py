"""Unit tests for the TrueLayer Data API v3 HTTP client (mocked; no live calls)."""

from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

from app.integrations import truelayer_client as tl
from app.integrations.truelayer_client import (
    TrueLayerAPIError,
    TrueLayerClient,
    TrueLayerConfigError,
    TrueLayerSettings,
    TrueLayerTimeoutError,
    load_truelayer_settings,
)


def _settings(*, environment: str = "sandbox") -> TrueLayerSettings:
    return TrueLayerSettings(
        client_id="test-client-id",
        client_secret="super-secret-value",
        environment=environment,
        api_base_url=tl._API_BASE_URLS[environment],
        auth_base_url=tl._AUTH_BASE_URLS[environment],
    )


def _token_response() -> dict[str, Any]:
    return {
        "access_token": "secret-access-token-value",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "data",
    }


class _Router:
    """Simple path-based mock for httpx.MockTransport."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self._routes: dict[tuple[str, str], Any] = {}

    def route(
        self,
        method: str,
        url_suffix: str,
        response: httpx.Response | Exception,
    ) -> None:
        self._routes[(method.upper(), url_suffix)] = response

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        key = None
        for (method, suffix), response in self._routes.items():
            if request.method == method and str(request.url).endswith(suffix):
                key = (method, suffix)
                break
            if request.method == method and suffix in str(request.url):
                key = (method, suffix)
                break
        if key is None:
            return httpx.Response(404, json={"title": "Not Found", "detail": "no route"})
        response = self._routes[key]
        if isinstance(response, Exception):
            raise response
        return response


def _client_with_router(router: _Router, *, environment: str = "sandbox") -> TrueLayerClient:
    client = TrueLayerClient(settings=_settings(environment=environment))
    client._http = httpx.Client(transport=httpx.MockTransport(router))
    return client


def test_missing_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "TRUELAYER_CLIENT_ID",
        "TRUELAYER_CLIENT_SECRET",
        "TRUELAYER_ENVIRONMENT",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(TrueLayerConfigError, match="Missing required TrueLayer"):
        load_truelayer_settings()


def test_sandbox_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUELAYER_CLIENT_ID", "cid")
    monkeypatch.setenv("TRUELAYER_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("TRUELAYER_ENVIRONMENT", "sandbox")

    settings = load_truelayer_settings()
    assert settings.api_base_url == "https://api.truelayer-sandbox.com"
    assert settings.auth_base_url == "https://auth.truelayer-sandbox.com"


def test_live_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUELAYER_CLIENT_ID", "cid")
    monkeypatch.setenv("TRUELAYER_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("TRUELAYER_ENVIRONMENT", "live")

    settings = load_truelayer_settings()
    assert settings.api_base_url == "https://api.truelayer.com"
    assert settings.auth_base_url == "https://auth.truelayer.com"


def test_invalid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUELAYER_CLIENT_ID", "cid")
    monkeypatch.setenv("TRUELAYER_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("TRUELAYER_ENVIRONMENT", "staging")

    with pytest.raises(TrueLayerConfigError, match="TRUELAYER_ENVIRONMENT"):
        load_truelayer_settings()


def test_successful_access_token_request() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    client = _client_with_router(router)

    token = client.get_access_token()
    assert token.access_token == "secret-access-token-value"
    assert token.expires_in == 3600

    # Reuse cached token — no second auth call.
    again = client.get_access_token()
    assert again.access_token == "secret-access-token-value"
    assert sum(1 for c in router.calls if c.url.path.endswith("/connect/token")) == 1

    auth_call = router.calls[0]
    body = {k: v[0] for k, v in parse_qs(auth_call.content.decode()).items()}
    assert body["grant_type"] == "client_credentials"
    assert body["scope"] == "data"
    assert body["client_id"] == "test-client-id"
    assert body["client_secret"] == "super-secret-value"


def test_failed_access_token_request_hides_secrets() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(
            401,
            json={
                "error": "invalid_client",
                "error_description": "client_secret super-secret-value rejected",
            },
        ),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerAPIError) as exc_info:
        client.get_access_token()

    message = str(exc_info.value)
    assert exc_info.value.status_code == 401
    assert "super-secret-value" not in message
    assert "secret-access-token-value" not in message


def test_successful_connection_creation() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "POST",
        "/v3/data-connections",
        httpx.Response(
            201,
            json={
                "id": "conn-123",
                "status": "authorization_required",
                "user": {"id": "user-1"},
                "hosted_page": {
                    "uri": "https://app.truelayer.com/data/conn-123",
                },
            },
            headers={"Tl-Trace-Id": "trace-abc"},
        ),
    )
    client = _client_with_router(router)

    connection = client.create_connection(
        {
            "scopes": ["accounts", "transactions"],
            "provider_selection": {"type": "user_selected"},
            "user": {"name": "Jane Smith", "email": "jane@example.com"},
            "user_consent": {"type": "authorization_flow_captured"},
            "hosted_page": {
                "type": "authorization_flow",
                "return_uri": "https://example.com/callback",
            },
        }
    )

    assert connection.id == "conn-123"
    assert connection.status == "authorization_required"
    assert connection.user_id == "user-1"
    assert connection.hosted_page_uri.endswith("conn-123")

    api_call = next(c for c in router.calls if "/v3/data-connections" in str(c.url))
    assert api_call.headers["Authorization"] == "Bearer secret-access-token-value"


def test_failed_connection_creation() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "POST",
        "/v3/data-connections",
        httpx.Response(
            400,
            json={
                "title": "Invalid Parameters",
                "detail": "The request body was invalid.",
                "status": 400,
            },
            headers={"Tl-Trace-Id": "trace-bad"},
        ),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerAPIError) as exc_info:
        client.create_connection({"scopes": []})

    assert exc_info.value.status_code == 400
    assert exc_info.value.trace_id == "trace-bad"
    assert "secret-access-token-value" not in str(exc_info.value)


def test_successful_account_retrieval() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "GET",
        "/v3/connected-accounts",
        httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "acc-1",
                        "type": "account",
                        "account_type": "current",
                        "customer_segment": "retail",
                        "currency": "GBP",
                        "account_identifiers": [
                            {
                                "type": "sort_code_account_number",
                                "sort_code": "560029",
                                "account_number": "26207729",
                            }
                        ],
                        "account_holder_names": ["John Smith"],
                        "bic": "MONZGB2LXXX",
                    }
                ],
                "pagination": {"next_cursor": None},
            },
        ),
    )
    client = _client_with_router(router)

    accounts = client.list_connected_accounts("conn-123")
    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"
    assert accounts[0].currency == "GBP"
    assert accounts[0].account_identifiers[0].sort_code == "560029"

    api_call = next(c for c in router.calls if "/v3/connected-accounts" in str(c.url))
    assert api_call.headers["Connection-Id"] == "conn-123"


def test_failed_account_retrieval() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "GET",
        "/v3/connected-accounts",
        httpx.Response(
            403,
            json={"title": "Forbidden", "detail": "Connection not authorised"},
        ),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerAPIError) as exc_info:
        client.list_connected_accounts("conn-123")
    assert exc_info.value.status_code == 403


def test_successful_transaction_retrieval() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "POST",
        "/transactions/requests",
        httpx.Response(
            202,
            json={"id": "req-1", "status": "pending"},
        ),
    )
    router.route(
        "GET",
        "/transactions/requests/req-1",
        httpx.Response(
            200,
            json={
                "id": "req-1",
                "status": "completed",
                "result": {
                    "items": [
                        {
                            "id": "tx-1",
                            "timestamp": "2025-04-01T12:34:56Z",
                            "description": "Salary",
                            "currency": "GBP",
                            "amount_in_minor": 250000,
                            "status": "settled",
                            "enrichment": {
                                "merchant_name": "Employer Ltd",
                                "transaction_category": {
                                    "category_code": "income",
                                    "category_name": "Income",
                                },
                            },
                        }
                    ],
                    "pagination": {"next_cursor": None},
                },
            },
        ),
    )
    client = _client_with_router(router)

    pending = client.create_transactions_request(
        "conn-123",
        "acc-1",
        from_date=date(2025, 4, 1),
        to_date=date(2025, 4, 30),
    )
    assert pending.status == "pending"
    assert pending.id == "req-1"

    completed = client.get_transactions_request("conn-123", "acc-1", "req-1")
    assert completed.status == "completed"
    assert len(completed.items) == 1
    assert completed.items[0].amount_in_minor == 250000
    assert completed.items[0].merchant_name == "Employer Ltd"


@pytest.mark.parametrize("status_code", [401, 403, 404, 429, 500, 502])
def test_truelayer_error_status_codes(status_code: int) -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "GET",
        "/v3/connected-accounts",
        httpx.Response(
            status_code,
            json={
                "title": "Error",
                "detail": f"failed with {status_code}",
            },
            headers={"Tl-Trace-Id": f"trace-{status_code}"},
        ),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerAPIError) as exc_info:
        client.list_connected_accounts("conn-123")

    assert exc_info.value.status_code == status_code
    assert exc_info.value.trace_id == f"trace-{status_code}"
    assert "secret-access-token-value" not in str(exc_info.value)
    assert "super-secret-value" not in str(exc_info.value)


def test_timeout() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.TimeoutException("timed out"),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerTimeoutError):
        client.get_access_token()


def test_error_message_never_contains_token_or_secret() -> None:
    router = _Router()
    router.route(
        "POST",
        "/connect/token",
        httpx.Response(200, json=_token_response()),
    )
    router.route(
        "POST",
        "/v3/data-connections",
        httpx.Response(
            500,
            json={
                "title": "Unknown Error",
                "detail": (
                    "access_token=secret-access-token-value "
                    "client_secret=super-secret-value"
                ),
            },
        ),
    )
    client = _client_with_router(router)

    with pytest.raises(TrueLayerAPIError) as exc_info:
        client.create_connection({"scopes": ["accounts"]})

    message = str(exc_info.value)
    assert "secret-access-token-value" not in message
    assert "super-secret-value" not in message
    assert "[redacted]" in message
