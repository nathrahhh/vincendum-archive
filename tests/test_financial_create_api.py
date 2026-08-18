from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
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
            ClientFinancialORM.__table__,
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
                ClientFinancialORM.__table__,
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    lender = LenderORM(id=1, name="Lender A", slug="lender-a")
    client_2 = ClientORM(
        id=2,
        name="Client Two",
        industry="tech",
        credit_limit=100_000.0,
        lender_id=1,
    )
    client_3 = ClientORM(
        id=3,
        name="Client Three",
        industry="retail",
        credit_limit=50_000.0,
        lender_id=1,
    )
    client_user = UserORM(
        id=9,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=1,
        client_id=2,
    )
    unlinked_user = UserORM(
        id=10,
        email="unlinked@example.com",
        auth0_user_id="auth0|unlinked",
        role="client",
        lender_id=None,
        client_id=None,
    )
    db_session.add_all([lender, client_2, client_3, client_user, unlinked_user])
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


def _unlinked_client_user() -> UserORM:
    return UserORM(
        id=10,
        email="unlinked@example.com",
        auth0_user_id="auth0|unlinked",
        role="client",
        lender_id=None,
        client_id=None,
    )


def _override(user: UserORM, db: Session) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _payload(**overrides: object) -> dict:
    data: dict = {
        "month": "2026-03-01",
        "revenue": 10_000,
        "cogs": 4_000,
        "gross_profit": 6_000,
        "opex": 2_000,
        "cash_balance": 5_000,
    }
    data.update(overrides)
    return data


def test_client_can_create_pending_financial(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post("/client/me/financials", json=_payload())
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    record = payload["record"]
    assert record["client_id"] == 2
    assert record["status"] == "PENDING"
    assert record["month"] == "2026-03-01"
    assert record["revenue"] == 10_000
    assert "client_id" not in _payload()

    stored = seeded_db.execute(select(ClientFinancialORM)).scalar_one()
    assert stored.client_id == 2
    assert stored.status == "PENDING"
    assert stored.month == date(2026, 3, 1)


def test_create_financial_request_does_not_require_client_id(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post("/client/me/financials", json=_payload())
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["record"]["client_id"] == 2


def test_create_financial_ignores_attempted_foreign_client_id(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post(
            "/client/me/financials",
            json=_payload(client_id=3),
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    record = response.json()["record"]
    assert record["client_id"] == 2
    assert record["status"] == "PENDING"

    stored = seeded_db.execute(select(ClientFinancialORM)).scalar_one()
    assert stored.client_id == 2


def test_client_without_client_id_cannot_create_financial(seeded_db: Session):
    client = _override(_unlinked_client_user(), seeded_db)
    try:
        response = client.post("/client/me/financials", json=_payload())
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert seeded_db.execute(select(ClientFinancialORM)).scalars().all() == []


def test_duplicate_month_returns_409(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        first = client.post("/client/me/financials", json=_payload())
        second = client.post("/client/me/financials", json=_payload())
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]
