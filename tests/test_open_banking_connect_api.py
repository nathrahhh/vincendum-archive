"""API tests for starting an Open Banking connection (TrueLayer mocked)."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.open_banking import get_open_banking_service
from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.integrations.truelayer_client import DataConnection, TrueLayerAPIError
from app.main import app
from app.models.bank_connection import BankConnectionORM
from app.models.client import ClientORM
from app.models.lender import LenderORM
from app.models.user import UserORM


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
            UserORM.__table__,
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
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    db_session.add(LenderORM(id=1, name="Lender A", slug="lender-a"))
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
        UserORM(
            id=9,
            email="client@example.com",
            auth0_user_id="auth0|client",
            role="client",
            lender_id=1,
            client_id=2,
        )
    )
    db_session.add(
        UserORM(
            id=8,
            email="admin@example.com",
            auth0_user_id="auth0|admin",
            role="admin",
            lender_id=1,
            client_id=None,
        )
    )
    db_session.commit()
    return db_session


def _client_user() -> UserORM:
    return UserORM(
        id=9,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=1,
        client_id=2,
    )


def _admin_user() -> UserORM:
    return UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=1,
        client_id=None,
    )


def _override(
    user: UserORM | None,
    db: Session,
    *,
    open_banking: MagicMock | None = None,
) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if user is None:
        def _unauthenticated() -> None:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user] = _unauthenticated
    else:
        app.dependency_overrides[get_current_user] = lambda: user

    if open_banking is not None:
        app.dependency_overrides[get_open_banking_service] = lambda: open_banking

    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_open_banking_service, None)


@pytest.fixture(autouse=True)
def _env_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "TRUELAYER_REDIRECT_URI",
        "https://example.com/open-banking/callback",
    )
    monkeypatch.setenv(
        "OPEN_BANKING_FRONTEND_CALLBACK_URL",
        "https://app.example.com/open-banking/complete",
    )


def test_authenticated_client_can_start_connection(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.start_connection.return_value = DataConnection(
        id="tl-conn-abc",
        status="authorization_required",
        user_id="tl-user-1",
        hosted_page_uri="https://app.truelayer.com/data/tl-conn-abc",
    )
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.post("/client/me/open-banking/connect")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["bank_connection_id"] is not None
    assert body["truelayer_connection_id"] == "tl-conn-abc"
    assert body["status"] == "authorization_required"
    assert body["authorization_url"] == "https://app.truelayer.com/data/tl-conn-abc"

    mock_service.start_connection.assert_called_once()
    kwargs = mock_service.start_connection.call_args.kwargs
    assert kwargs["user_name"] == "Client Two"
    assert kwargs["user_email"] == "client@example.com"
    assert kwargs["return_uri"].startswith(
        "https://example.com/open-banking/callback?"
    )
    assert "state=" in kwargs["return_uri"]

    row = seeded_db.execute(
        select(BankConnectionORM).where(
            BankConnectionORM.truelayer_connection_id == "tl-conn-abc"
        )
    ).scalar_one()
    assert row.client_id == 2
    assert row.status == "authorization_required"
    assert row.id == body["bank_connection_id"]
    assert row.callback_state is not None
    assert row.callback_state in kwargs["return_uri"]


def test_unauthenticated_returns_401(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(None, seeded_db, open_banking=mock_service)
    try:
        response = client.post("/client/me/open-banking/connect")
    finally:
        _clear_overrides()

    assert response.status_code == 401
    mock_service.start_connection.assert_not_called()


def test_admin_cannot_start_connection(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(_admin_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.post("/client/me/open-banking/connect")
    finally:
        _clear_overrides()

    assert response.status_code == 403
    mock_service.start_connection.assert_not_called()


def test_truelayer_failure_handled(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.start_connection.side_effect = TrueLayerAPIError(
        "provider rejected",
        status_code=400,
        trace_id="trace-x",
    )
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.post("/client/me/open-banking/connect")
    finally:
        _clear_overrides()

    assert response.status_code == 400
    assert "secret" not in response.text.lower()
    assert seeded_db.execute(select(BankConnectionORM)).scalars().all() == []


def test_database_failure_rolls_back_without_leaking_secrets(
    seeded_db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_service = MagicMock()
    mock_service.start_connection.return_value = DataConnection(
        id="tl-conn-fail-persist",
        status="authorization_required",
        hosted_page_uri="https://app.truelayer.com/data/x",
    )

    original_commit = seeded_db.commit

    def boom() -> None:
        raise RuntimeError("db down access_token=secret-token client_secret=shh")

    monkeypatch.setattr(seeded_db, "commit", boom)

    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.post("/client/me/open-banking/connect")
    finally:
        monkeypatch.setattr(seeded_db, "commit", original_commit)
        _clear_overrides()

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to save bank connection"
    assert "secret-token" not in response.text
    assert "shh" not in response.text
    assert "access_token" not in response.text

    seeded_db.rollback()
    assert seeded_db.execute(select(BankConnectionORM)).scalars().all() == []
