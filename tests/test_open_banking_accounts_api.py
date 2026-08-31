"""API tests for Open Banking account sync/list (TrueLayer mocked)."""

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
from app.integrations.truelayer_client import BankAccount, TrueLayerAPIError
from app.main import app
from app.models.bank_account import BankAccountORM
from app.models.bank_connection import BankConnectionORM
from app.models.client import ClientORM
from app.models.lender import LenderORM
from app.models.user import UserORM
from app.services.open_banking_service import STATUS_AUTHORIZED


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
            BankAccountORM.__table__,
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
                BankAccountORM.__table__,
                BankConnectionORM.__table__,
                UserORM.__table__,
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
        ClientORM(
            id=3,
            name="Client Three",
            industry="retail",
            credit_limit=50_000.0,
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
            id=10,
            email="other-client@example.com",
            auth0_user_id="auth0|other-client",
            role="client",
            lender_id=1,
            client_id=3,
        )
    )
    db_session.add(
        BankConnectionORM(
            id=10,
            client_id=2,
            truelayer_connection_id="tl-conn-authorized",
            callback_state="state-auth",
            status=STATUS_AUTHORIZED,
        )
    )
    db_session.add(
        BankConnectionORM(
            id=11,
            client_id=2,
            truelayer_connection_id="tl-conn-pending",
            callback_state="state-pending",
            status="authorization_required",
        )
    )
    db_session.add(
        BankConnectionORM(
            id=20,
            client_id=3,
            truelayer_connection_id="tl-conn-other",
            callback_state="state-other",
            status=STATUS_AUTHORIZED,
        )
    )
    db_session.add(
        BankAccountORM(
            id=99,
            bank_connection_id=20,
            truelayer_account_id="acc-other-secret",
            account_type="TRANSACTION",
            currency="GBP",
        )
    )
    db_session.commit()
    return db_session


def _client_user(*, user_id: int = 9, client_id: int = 2) -> UserORM:
    return UserORM(
        id=user_id,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=1,
        client_id=client_id,
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


def _provider_accounts() -> list[BankAccount]:
    return [
        BankAccount(
            id="acc-1",
            type="account",
            currency="GBP",
            account_type="TRANSACTION",
            account_identifiers=(),
        ),
        BankAccount(
            id="acc-2",
            type="account",
            currency="EUR",
            account_type="SAVINGS",
            account_identifiers=(),
        ),
    ]


def test_authenticated_client_retrieves_and_syncs_accounts(
    seeded_db: Session,
) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {row["truelayer_account_id"] for row in body} == {"acc-1", "acc-2"}
    assert all(row["bank_connection_id"] == 10 for row in body)
    assert all(
        set(row.keys())
        == {
            "id",
            "bank_connection_id",
            "truelayer_account_id",
            "account_type",
            "currency",
            "created_at",
            "updated_at",
        }
        for row in body
    )
    assert "iban" not in response.text.lower()
    assert "sort_code" not in response.text.lower()
    assert "account_number" not in response.text.lower()

    mock_service.list_accounts.assert_called_once_with(
        "tl-conn-authorized",
        user_ip="testclient",
    )

    rows = seeded_db.execute(select(BankAccountORM)).scalars().all()
    # Includes other client's pre-seeded account (id=99) plus two new ones.
    client_rows = [row for row in rows if row.bank_connection_id == 10]
    assert len(client_rows) == 2


def test_accounts_created_on_first_sync(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    assert (
        seeded_db.execute(
            select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
        )
        .scalars()
        .all()
        == []
    )

    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    rows = seeded_db.execute(
        select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
    ).scalars().all()
    assert len(rows) == 2
    assert {row.truelayer_account_id for row in rows} == {"acc-1", "acc-2"}


def test_existing_accounts_updated_not_duplicated(seeded_db: Session) -> None:
    seeded_db.add(
        BankAccountORM(
            bank_connection_id=10,
            truelayer_account_id="acc-1",
            account_type="OLD",
            currency="USD",
        )
    )
    seeded_db.commit()

    mock_service = MagicMock()
    mock_service.list_accounts.return_value = [
        BankAccount(
            id="acc-1",
            type="account",
            currency="GBP",
            account_type="TRANSACTION",
        ),
    ]
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    rows = seeded_db.execute(
        select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].truelayer_account_id == "acc-1"
    assert rows[0].account_type == "TRANSACTION"
    assert rows[0].currency == "GBP"


def test_repeated_requests_do_not_create_duplicates(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        first = client.get("/client/me/open-banking/accounts")
        second = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 200
    rows = seeded_db.execute(
        select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
    ).scalars().all()
    assert len(rows) == 2
    assert mock_service.list_accounts.call_count == 2


def test_unauthorized_connections_are_not_synchronized(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    mock_service.list_accounts.assert_called_once_with(
        "tl-conn-authorized",
        user_ip="testclient",
    )
    assert all(
        call.args[0] != "tl-conn-pending"
        for call in mock_service.list_accounts.call_args_list
    )


def test_client_cannot_access_another_clients_accounts(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert all(row["bank_connection_id"] == 10 for row in body)
    assert all(row["truelayer_account_id"] != "acc-other-secret" for row in body)
    assert all(
        call.args[0] != "tl-conn-other"
        for call in mock_service.list_accounts.call_args_list
    )


def test_truelayer_provider_error_handled(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.side_effect = TrueLayerAPIError(
        "provider rejected",
        status_code=403,
        trace_id="trace-accounts",
    )
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Open Banking provider rejected the accounts request"
    )
    assert "trace-accounts" not in response.text
    assert (
        seeded_db.execute(
            select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
        )
        .scalars()
        .all()
        == []
    )


def test_database_failure_rolls_back(
    seeded_db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_service = MagicMock()
    mock_service.list_accounts.return_value = _provider_accounts()
    original_commit = seeded_db.commit

    def boom() -> None:
        raise RuntimeError("db down access_token=secret-token")

    monkeypatch.setattr(seeded_db, "commit", boom)
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        monkeypatch.setattr(seeded_db, "commit", original_commit)
        _clear_overrides()

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to save bank accounts"
    assert "secret-token" not in response.text

    seeded_db.rollback()
    assert (
        seeded_db.execute(
            select(BankAccountORM).where(BankAccountORM.bank_connection_id == 10)
        )
        .scalars()
        .all()
        == []
    )


def test_unauthenticated_returns_401(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(None, seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts")
    finally:
        _clear_overrides()

    assert response.status_code == 401
    mock_service.list_accounts.assert_not_called()
