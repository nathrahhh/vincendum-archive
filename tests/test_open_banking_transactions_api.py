"""API tests for Open Banking transaction sync (TrueLayer mocked)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.open_banking import get_open_banking_service
from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.integrations.truelayer_client import TrueLayerAPIError, TrueLayerError
from app.main import app
from app.models.bank_account import BankAccountORM
from app.models.bank_connection import BankConnectionORM
from app.models.bank_transaction import BankTransactionORM
from app.models.client import ClientORM
from app.models.lender import LenderORM
from app.models.user import UserORM
from app.services.open_banking_service import STATUS_AUTHORIZED, SyncedTransaction


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
            BankTransactionORM.__table__,
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
                BankTransactionORM.__table__,
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
        BankConnectionORM(
            id=10,
            client_id=2,
            truelayer_connection_id="tl-conn-authorized",
            status=STATUS_AUTHORIZED,
        )
    )
    db_session.add(
        BankConnectionORM(
            id=11,
            client_id=2,
            truelayer_connection_id="tl-conn-pending",
            status="authorization_required",
        )
    )
    db_session.add(
        BankConnectionORM(
            id=20,
            client_id=3,
            truelayer_connection_id="tl-conn-other",
            status=STATUS_AUTHORIZED,
        )
    )
    db_session.add(
        BankAccountORM(
            id=100,
            bank_connection_id=10,
            truelayer_account_id="tl-acc-own",
            currency="GBP",
        )
    )
    db_session.add(
        BankAccountORM(
            id=101,
            bank_connection_id=11,
            truelayer_account_id="tl-acc-unauthorized",
            currency="GBP",
        )
    )
    db_session.add(
        BankAccountORM(
            id=200,
            bank_connection_id=20,
            truelayer_account_id="tl-acc-other",
            currency="GBP",
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


def _synced(*items: SyncedTransaction) -> list[SyncedTransaction]:
    return list(items)


def _txn(
    tl_id: str,
    *,
    amount: str = "10.00",
    description: str = "Payment",
    transaction_type: str = "booked",
) -> SyncedTransaction:
    return SyncedTransaction(
        truelayer_transaction_id=tl_id,
        booking_date=datetime(2026, 1, 10, tzinfo=timezone.utc),
        value_date=None,
        amount=Decimal(amount),
        currency="GBP",
        description=description,
        transaction_type=transaction_type,
    )


def test_client_can_sync_own_account_transactions(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.default_transaction_date_range.return_value = (
        datetime(2025, 10, 1).date(),
        datetime(2026, 1, 1).date(),
    )
    mock_service.fetch_account_transactions.return_value = _synced(
        _txn("A"),
        _txn("B", amount="20.00"),
        _txn("C", amount="30.00"),
    )
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/100/transactions")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert {row["truelayer_transaction_id"] for row in body} == {"A", "B", "C"}
    assert all(row["bank_account_id"] == 100 for row in body)
    mock_service.fetch_account_transactions.assert_called_once()
    kwargs = mock_service.fetch_account_transactions.call_args
    assert kwargs.args[0] == "tl-conn-authorized"
    assert kwargs.args[1] == "tl-acc-own"


def test_client_cannot_access_another_clients_transactions(
    seeded_db: Session,
) -> None:
    mock_service = MagicMock()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/200/transactions")
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "Bank account not found"
    mock_service.fetch_account_transactions.assert_not_called()


def test_repeated_sync_does_not_duplicate(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.default_transaction_date_range.return_value = (
        datetime(2025, 10, 1).date(),
        datetime(2026, 1, 1).date(),
    )
    mock_service.fetch_account_transactions.side_effect = [
        _synced(_txn("A"), _txn("B"), _txn("C")),
        _synced(
            _txn("A", description="Updated A"),
            _txn("B"),
            _txn("C"),
            _txn("D", amount="40.00"),
        ),
    ]
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        first = client.get("/client/me/open-banking/accounts/100/transactions")
        second = client.get("/client/me/open-banking/accounts/100/transactions")
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 200
    rows = seeded_db.execute(
        select(BankTransactionORM).where(BankTransactionORM.bank_account_id == 100)
    ).scalars().all()
    assert len(rows) == 4
    assert {row.truelayer_transaction_id for row in rows} == {"A", "B", "C", "D"}
    updated = next(row for row in rows if row.truelayer_transaction_id == "A")
    assert updated.description == "Updated A"


def test_unauthorized_connection_rejected(seeded_db: Session) -> None:
    mock_service = MagicMock()
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/101/transactions")
    finally:
        _clear_overrides()

    assert response.status_code == 409
    mock_service.fetch_account_transactions.assert_not_called()


@pytest.mark.parametrize(
    ("status_code", "expected_http"),
    [
        (401, 401),
        (403, 403),
        (404, 404),
        (429, 429),
        (500, 502),
    ],
)
def test_provider_api_errors(
    seeded_db: Session,
    status_code: int,
    expected_http: int,
) -> None:
    mock_service = MagicMock()
    mock_service.default_transaction_date_range.return_value = (
        datetime(2025, 10, 1).date(),
        datetime(2026, 1, 1).date(),
    )
    mock_service.fetch_account_transactions.side_effect = TrueLayerAPIError(
        "provider rejected",
        status_code=status_code,
        trace_id="trace-txn",
    )
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/100/transactions")
    finally:
        _clear_overrides()

    assert response.status_code == expected_http
    assert "trace-txn" not in response.text


def test_generic_provider_error(seeded_db: Session) -> None:
    mock_service = MagicMock()
    mock_service.default_transaction_date_range.return_value = (
        datetime(2025, 10, 1).date(),
        datetime(2026, 1, 1).date(),
    )
    mock_service.fetch_account_transactions.side_effect = TrueLayerError("network")
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/100/transactions")
    finally:
        _clear_overrides()

    assert response.status_code == 502
    assert response.json()["detail"] == "Open Banking provider error"


def test_database_failure_rolls_back(
    seeded_db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_service = MagicMock()
    mock_service.default_transaction_date_range.return_value = (
        datetime(2025, 10, 1).date(),
        datetime(2026, 1, 1).date(),
    )
    mock_service.fetch_account_transactions.return_value = _synced(_txn("A"))
    original_commit = seeded_db.commit

    def boom() -> None:
        raise RuntimeError("db down access_token=secret-token")

    monkeypatch.setattr(seeded_db, "commit", boom)
    client = _override(_client_user(), seeded_db, open_banking=mock_service)
    try:
        response = client.get("/client/me/open-banking/accounts/100/transactions")
    finally:
        monkeypatch.setattr(seeded_db, "commit", original_commit)
        _clear_overrides()

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to save bank transactions"
    assert "secret-token" not in response.text
    seeded_db.rollback()
    assert (
        seeded_db.execute(
            select(BankTransactionORM).where(BankTransactionORM.bank_account_id == 100)
        )
        .scalars()
        .all()
        == []
    )
