"""TrueLayer Data API v3 HTTP client.

Pure HTTP integration — no FastAPI routes, ORM, or repayment logic.

Environment variables:

- ``TRUELAYER_CLIENT_ID``
- ``TRUELAYER_CLIENT_SECRET``
- ``TRUELAYER_ENVIRONMENT`` (``sandbox`` | ``live``)

Documented Data API v3 endpoints implemented here:

- ``POST {auth}/connect/token`` (client_credentials, scope=data)
- ``POST /v3/data-connections``
- ``GET /v3/connected-accounts``
- ``POST /v3/connected-accounts/{account_id}/transactions/requests``
- ``GET /v3/connected-accounts/{account_id}/transactions/requests/{request_id}``

Account balances are **not** implemented: the current TrueLayer reference only
documents balance retrieval under Data API v1
(``/data/v1/accounts/{account_id}/balance``), not Data API v3.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30.0
_TOKEN_EXPIRY_SKEW_SECONDS = 60.0

_API_BASE_URLS = {
    "sandbox": "https://api.truelayer-sandbox.com",
    "live": "https://api.truelayer.com",
}
_AUTH_BASE_URLS = {
    "sandbox": "https://auth.truelayer-sandbox.com",
    "live": "https://auth.truelayer.com",
}

_SENSITIVE_SUBSTRINGS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
)


class TrueLayerConfigError(RuntimeError):
    """Raised when TrueLayer environment configuration is missing or invalid."""


class TrueLayerError(Exception):
    """Base error for TrueLayer client failures (never includes secrets)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
        title: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id
        self.title = title


class TrueLayerAPIError(TrueLayerError):
    """Raised for non-success HTTP responses from TrueLayer."""


class TrueLayerTimeoutError(TrueLayerError):
    """Raised when a TrueLayer request times out."""


class TrueLayerResponseError(TrueLayerError):
    """Raised when a TrueLayer response cannot be parsed as expected."""


@dataclass(frozen=True)
class AccessToken:
    access_token: str
    token_type: str
    expires_in: int
    scope: str | None = None


@dataclass(frozen=True)
class DataConnection:
    id: str
    status: str
    user_id: str | None = None
    hosted_page_uri: str | None = None


@dataclass(frozen=True)
class AccountIdentifier:
    type: str
    sort_code: str | None = None
    account_number: str | None = None
    iban: str | None = None


@dataclass(frozen=True)
class BankAccount:
    id: str
    type: str
    currency: str | None = None
    account_type: str | None = None
    customer_segment: str | None = None
    account_holder_names: tuple[str, ...] = ()
    account_identifiers: tuple[AccountIdentifier, ...] = ()
    bic: str | None = None


@dataclass(frozen=True)
class BankTransaction:
    id: str
    timestamp: str
    description: str
    currency: str
    amount_in_minor: int
    status: str
    merchant_name: str | None = None
    category_code: str | None = None
    category_name: str | None = None


@dataclass(frozen=True)
class TransactionsRequestResult:
    id: str
    status: str
    items: tuple[BankTransaction, ...] = ()
    next_cursor: str | None = None
    failure_reason: str | None = None


@dataclass
class TrueLayerSettings:
    client_id: str
    client_secret: str
    environment: str
    api_base_url: str
    auth_base_url: str


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise TrueLayerConfigError(
            f"Missing required TrueLayer configuration: {name}."
        )
    return value


def load_truelayer_settings() -> TrueLayerSettings:
    """Load and validate TrueLayer settings from the environment."""
    environment = _require_env("TRUELAYER_ENVIRONMENT").lower()
    if environment not in _API_BASE_URLS:
        raise TrueLayerConfigError(
            "Invalid TRUELAYER_ENVIRONMENT="
            f"{environment!r}; expected 'sandbox' or 'live'."
        )
    return TrueLayerSettings(
        client_id=_require_env("TRUELAYER_CLIENT_ID"),
        client_secret=_require_env("TRUELAYER_CLIENT_SECRET"),
        environment=environment,
        api_base_url=_API_BASE_URLS[environment],
        auth_base_url=_AUTH_BASE_URLS[environment],
    )


def _redact_text(value: str) -> str:
    lowered = value.lower()
    for needle in _SENSITIVE_SUBSTRINGS:
        if needle in lowered:
            return "[redacted]"
    return value


def _safe_error_detail(payload: Any) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    for key in ("detail", "title", "error_description", "error"):
        value = payload.get(key)
        if value is None:
            continue
        return _redact_text(str(value))
    return None


@dataclass
class TrueLayerClient:
    """Synchronous HTTP client for TrueLayer Data API v3."""

    settings: TrueLayerSettings
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    _http: httpx.Client = field(init=False, repr=False)
    _cached_token: str | None = field(default=None, init=False, repr=False)
    _token_expires_at: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._http = httpx.Client(timeout=self.timeout_seconds)

    @classmethod
    def from_env(
        cls,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> TrueLayerClient:
        return cls(
            settings=load_truelayer_settings(),
            timeout_seconds=timeout_seconds,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> TrueLayerClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def clear_token_cache(self) -> None:
        self._cached_token = None
        self._token_expires_at = 0.0

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_access_token(self, *, force_refresh: bool = False) -> AccessToken:
        """Obtain (or reuse) a client-credentials access token with scope=data."""
        now = time.monotonic()
        if (
            not force_refresh
            and self._cached_token is not None
            and now < self._token_expires_at
        ):
            return AccessToken(
                access_token=self._cached_token,
                token_type="Bearer",
                expires_in=max(0, int(self._token_expires_at - now)),
            )

        url = f"{self.settings.auth_base_url}/connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "scope": "data",
        }
        payload = self._request_json(
            "POST",
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            authenticated=False,
        )
        try:
            token = AccessToken(
                access_token=str(payload["access_token"]),
                token_type=str(payload.get("token_type", "Bearer")),
                expires_in=int(payload["expires_in"]),
                scope=str(payload["scope"]) if payload.get("scope") else "data",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrueLayerResponseError(
                "Malformed access-token response from TrueLayer."
            ) from exc

        self._cached_token = token.access_token
        self._token_expires_at = (
            time.monotonic()
            + max(0, token.expires_in - _TOKEN_EXPIRY_SKEW_SECONDS)
        )
        return token

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def create_connection(
        self,
        payload: Mapping[str, Any],
        *,
        user_ip: str | None = None,
        user_agent: str | None = None,
    ) -> DataConnection:
        """Create a Data V3 connection via ``POST /v3/data-connections``."""
        headers: dict[str, str] = {}
        if user_ip:
            headers["Tl-User-Ip"] = user_ip
        if user_agent:
            headers["User-Agent"] = user_agent

        body = self._request_json(
            "POST",
            f"{self.settings.api_base_url}/v3/data-connections",
            json_body=dict(payload),
            headers=headers,
            expected_statuses={201},
        )
        try:
            hosted = body.get("hosted_page") or {}
            user = body.get("user") or {}
            return DataConnection(
                id=str(body["id"]),
                status=str(body["status"]),
                user_id=str(user["id"]) if user.get("id") else None,
                hosted_page_uri=(
                    str(hosted["uri"]) if hosted.get("uri") else None
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrueLayerResponseError(
                "Malformed create-connection response from TrueLayer."
            ) from exc

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    def list_connected_accounts(
        self,
        connection_id: str,
        *,
        user_ip: str | None = None,
        account_type: str | None = None,
        cursor: str | None = None,
    ) -> list[BankAccount]:
        """List accounts for a connection via ``GET /v3/connected-accounts``."""
        headers = {"Connection-Id": connection_id}
        if user_ip:
            headers["Tl-User-Ip"] = user_ip

        params: dict[str, str] = {}
        if account_type:
            params["type"] = account_type
        if cursor:
            params["cursor"] = cursor

        body = self._request_json(
            "GET",
            f"{self.settings.api_base_url}/v3/connected-accounts",
            headers=headers,
            params=params or None,
            expected_statuses={200},
        )
        try:
            items = body.get("items") or []
            return [self._parse_account(item) for item in items]
        except (KeyError, TypeError, ValueError) as exc:
            raise TrueLayerResponseError(
                "Malformed connected-accounts response from TrueLayer."
            ) from exc

    # ------------------------------------------------------------------
    # Transactions (async request + poll)
    # ------------------------------------------------------------------

    def create_transactions_request(
        self,
        connection_id: str,
        account_id: str,
        *,
        from_date: date,
        to_date: date,
        cursor: str | None = None,
        page_size: int | None = None,
        enrichment: Mapping[str, Any] | None = None,
        user_ip: str | None = None,
    ) -> TransactionsRequestResult:
        """Create an async transactions request (``202`` / status=pending)."""
        headers = {"Connection-Id": connection_id}
        if user_ip:
            headers["Tl-User-Ip"] = user_ip

        payload: dict[str, Any] = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }
        if cursor is not None:
            payload["cursor"] = cursor
        if page_size is not None:
            payload["page_size"] = page_size
        if enrichment is not None:
            payload["enrichment"] = dict(enrichment)

        body = self._request_json(
            "POST",
            (
                f"{self.settings.api_base_url}/v3/connected-accounts/"
                f"{account_id}/transactions/requests"
            ),
            json_body=payload,
            headers=headers,
            expected_statuses={202},
        )
        return self._parse_transactions_request(body)

    def get_transactions_request(
        self,
        connection_id: str,
        account_id: str,
        request_id: str,
        *,
        user_ip: str | None = None,
    ) -> TransactionsRequestResult:
        """Poll/read a transactions request by id."""
        headers = {"Connection-Id": connection_id}
        if user_ip:
            headers["Tl-User-Ip"] = user_ip

        body = self._request_json(
            "GET",
            (
                f"{self.settings.api_base_url}/v3/connected-accounts/"
                f"{account_id}/transactions/requests/{request_id}"
            ),
            headers=headers,
            expected_statuses={200},
        )
        return self._parse_transactions_request(body)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _parse_account(self, item: Mapping[str, Any]) -> BankAccount:
        identifiers: list[AccountIdentifier] = []
        for raw in item.get("account_identifiers") or []:
            identifiers.append(
                AccountIdentifier(
                    type=str(raw.get("type", "")),
                    sort_code=raw.get("sort_code"),
                    account_number=raw.get("account_number"),
                    iban=raw.get("iban"),
                )
            )
        names = tuple(str(n) for n in (item.get("account_holder_names") or []))
        return BankAccount(
            id=str(item["id"]),
            type=str(item.get("type", "account")),
            currency=item.get("currency"),
            account_type=item.get("account_type"),
            customer_segment=item.get("customer_segment"),
            account_holder_names=names,
            account_identifiers=tuple(identifiers),
            bic=item.get("bic"),
        )

    def _parse_transaction(self, item: Mapping[str, Any]) -> BankTransaction:
        enrichment = item.get("enrichment") or {}
        category = enrichment.get("transaction_category") or {}
        return BankTransaction(
            id=str(item["id"]),
            timestamp=str(item["timestamp"]),
            description=str(item["description"]),
            currency=str(item["currency"]),
            amount_in_minor=int(item["amount_in_minor"]),
            status=str(item["status"]),
            merchant_name=enrichment.get("merchant_name"),
            category_code=category.get("category_code"),
            category_name=category.get("category_name"),
        )

    def _parse_transactions_request(
        self,
        body: Mapping[str, Any],
    ) -> TransactionsRequestResult:
        try:
            status = str(body["status"])
            request_id = str(body["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TrueLayerResponseError(
                "Malformed transactions-request response from TrueLayer."
            ) from exc

        if status == "completed":
            result = body.get("result") or {}
            items = tuple(
                self._parse_transaction(item)
                for item in (result.get("items") or [])
            )
            pagination = result.get("pagination") or {}
            return TransactionsRequestResult(
                id=request_id,
                status=status,
                items=items,
                next_cursor=pagination.get("next_cursor"),
            )

        if status == "failed":
            return TransactionsRequestResult(
                id=request_id,
                status=status,
                failure_reason=(
                    str(body["failure_reason"])
                    if body.get("failure_reason") is not None
                    else None
                ),
            )

        return TransactionsRequestResult(id=request_id, status=status)

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: Mapping[str, str] | None = None,
        authenticated: bool = True,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        request_headers = {**(headers or {})}
        if authenticated:
            token = self.get_access_token()
            request_headers["Authorization"] = f"Bearer {token.access_token}"

        try:
            response = self._http.request(
                method,
                url,
                headers=request_headers,
                params=params,
                json=json_body,
                data=data,
            )
        except httpx.TimeoutException as exc:
            raise TrueLayerTimeoutError(
                "TrueLayer request timed out.",
            ) from exc
        except httpx.HTTPError as exc:
            raise TrueLayerError(
                "TrueLayer request failed due to a network error.",
            ) from exc

        trace_id = response.headers.get("Tl-Trace-Id")
        if expected_statuses is None:
            expected_statuses = {200, 201, 202}

        if response.status_code not in expected_statuses:
            payload: Any
            try:
                payload = response.json()
            except ValueError:
                payload = None
            detail = _safe_error_detail(payload) or "TrueLayer API request failed."
            title = None
            if isinstance(payload, Mapping) and payload.get("title"):
                title = _redact_text(str(payload["title"]))
            logger.warning(
                "TrueLayer API error status=%s trace_id=%s title=%s detail=%s",
                response.status_code,
                trace_id,
                title,
                detail,
            )
            raise TrueLayerAPIError(
                detail,
                status_code=response.status_code,
                trace_id=trace_id,
                title=title,
            )

        if response.status_code == 204 or not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise TrueLayerResponseError(
                "TrueLayer returned a non-JSON response.",
                status_code=response.status_code,
                trace_id=trace_id,
            ) from exc

        if not isinstance(payload, dict):
            raise TrueLayerResponseError(
                "TrueLayer returned an unexpected JSON payload type.",
                status_code=response.status_code,
                trace_id=trace_id,
            )
        return payload


def parse_iso_date(value: str | date | datetime) -> date:
    """Helper for callers converting date inputs (not used by HTTP itself)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
