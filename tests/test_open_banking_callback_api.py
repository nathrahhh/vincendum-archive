"""API tests for the Open Banking TrueLayer return callback."""

from __future__ import annotations

import logging
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.open_banking import get_open_banking_service
from app.db import Base, get_db
from app.integrations.truelayer_client import TrueLayerAPIError
from app.main import app
from app.models.bank_connection import BankConnectionORM
from app.models.client import ClientORM
from app.models.lender import LenderORM
from app.services.open_banking_service import (
    STATUS_AUTHORIZED,
    STATUS_CANCELLED,
    STATUS_FAILED,
    ConnectionAuthorizationResult,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            ClientORM.__table__,
            BankConnectionORM.__table__,
        ],
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                BankConnectionORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    db_session.add(LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000))
    db_session.add(
        ClientORM(
            id=2,
            name="Client Two",
            industry="tech",
            credit_limit=100_000.0,
            lender_id=1,
        )
    )
    db_session.add(
        BankConnectionORM(
            id=10,
            client_id=2,
            truelayer_connection_id="tl-conn-abc",
            callback_state="state-secret-abc",
            status="authorization_required",
        )
    )
    db_session.commit()
    return db_session


def _override(
    db: Session,
    *,
    open_banking: MagicMock | None = None,
) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if open_banking is not None:
        app.dependency_overrides[get_open_banking_service] = lambda: open_banking
    return TestClient(app, follow_redirects=False)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_open_banking_service, None)


@pytest.fixture(autouse=True)
def _env_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "TRUELAYER_REDIRECT_URI",
        "https://example.com/client/open-banking/callback",
    )
    monkeypatch.setenv(
        "OPEN_BANKING_FRONTEND_CALLBACK_URL",
        "https://app.example.com/open-banking/complete",
    )


def test_successful_callback_updates_existing_connection(
    seeded_db: Session,
) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.return_value = (
        ConnectionAuthorizationResult(status=STATUS_AUTHORIZED, authorized=True)
    )
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={"state": "state-secret-abc"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://app.example.com/open-banking/complete?")
    assert "status=success" in location
    assert "bank_connection_id=10" in location

    mock_service.finalize_connection_authorization.assert_called_once_with(
        "tl-conn-abc",
        user_ip="testclient",
    )

    row = seeded_db.get(BankConnectionORM, 10)
    assert row is not None
    assert row.status == STATUS_AUTHORIZED
    assert (
        seeded_db.execute(select(BankConnectionORM)).scalars().all().__len__() == 1
    )


def test_cancelled_authorization_persists_cancelled_status(
    seeded_db: Session,
) -> None:
    mock_service = MagicMock()
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={
                "state": "state-secret-abc",
                "error": "access_denied",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 302
    assert "status=failure" in response.headers["location"]
    mock_service.finalize_connection_authorization.assert_not_called()

    row = seeded_db.get(BankConnectionORM, 10)
    assert row is not None
    assert row.status == STATUS_CANCELLED


def test_failed_authorization_when_provider_denies_access(
    seeded_db: Session,
) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.return_value = (
        ConnectionAuthorizationResult(status=STATUS_FAILED, authorized=False)
    )
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={"state": "state-secret-abc"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 302
    assert "status=failure" in response.headers["location"]
    row = seeded_db.get(BankConnectionORM, 10)
    assert row is not None
    assert row.status == STATUS_FAILED


def test_missing_callback_parameters_returns_400(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/open-banking/callback")
    finally:
        _clear_overrides()

    assert response.status_code == 400
    mock_service.finalize_connection_authorization.assert_not_called()


def test_unknown_truelayer_connection_id_returns_404(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={"connection_id": "tl-conn-unknown"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404
    mock_service.finalize_connection_authorization.assert_not_called()
    row = seeded_db.get(BankConnectionORM, 10)
    assert row is not None
    assert row.status == "authorization_required"


def test_database_failure_returns_safe_500(
    seeded_db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.return_value = (
        ConnectionAuthorizationResult(status=STATUS_AUTHORIZED, authorized=True)
    )

    original_commit = seeded_db.commit

    def boom() -> None:
        raise RuntimeError("db down access_token=secret-token")

    monkeypatch.setattr(seeded_db, "commit", boom)
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={"state": "state-secret-abc"},
        )
    finally:
        monkeypatch.setattr(seeded_db, "commit", original_commit)
        _clear_overrides()

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to update bank connection"
    assert "secret-token" not in response.text
    assert "access_token" not in response.text


def test_sensitive_callback_values_are_not_logged(
    seeded_db: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.return_value = (
        ConnectionAuthorizationResult(status=STATUS_AUTHORIZED, authorized=True)
    )
    client = _override(seeded_db, open_banking=mock_service)
    with caplog.at_level(logging.INFO, logger="app.api.routes.open_banking"):
        try:
            response = client.get(
                "/client/open-banking/callback",
                params={
                    "state": "state-secret-abc",
                    "code": "auth-code-should-never-be-logged",
                    "access_token": "token-should-never-be-logged",
                },
            )
        finally:
            _clear_overrides()

    assert response.status_code == 302
    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "auth-code-should-never-be-logged" not in joined
    assert "token-should-never-be-logged" not in joined
    assert "state-secret-abc" not in joined
    assert "bank_connection_id=10" in joined
    assert "client_id=2" in joined


def test_callback_does_not_duplicate_bank_connection(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.return_value = (
        ConnectionAuthorizationResult(status=STATUS_AUTHORIZED, authorized=True)
    )
    client = _override(seeded_db, open_banking=mock_service)
    try:
        first = client.get(
            "/client/open-banking/callback",
            params={
                "state": "state-secret-abc",
                "connection_id": "tl-conn-abc",
            },
        )
        second = client.get(
            "/client/open-banking/callback",
            params={
                "state": "state-secret-abc",
                "connection_id": "tl-conn-abc",
            },
        )
    finally:
        _clear_overrides()

    assert first.status_code == 302
    assert second.status_code == 302
    rows = seeded_db.execute(select(BankConnectionORM)).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == 10
    assert rows[0].status == STATUS_AUTHORIZED


def test_provider_api_error_returns_safe_502(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.finalize_connection_authorization.side_effect = TrueLayerAPIError(
        "upstream failed",
        status_code=500,
        trace_id="trace-z",
    )
    client = _override(seeded_db, open_banking=mock_service)
    try:
        response = client.get(
            "/client/open-banking/callback",
            params={"state": "state-secret-abc"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 502
    assert response.json()["detail"] == "Open Banking provider error"
    assert "trace-z" not in response.text
