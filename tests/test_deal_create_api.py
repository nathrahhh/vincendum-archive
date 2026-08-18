from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.client import ClientORM
from app.models.deal import DealORM
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
            DealORM.__table__,
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
                DealORM.__table__,
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


def _client_user(*, client_id: int | None = 2, lender_id: int | None = 1) -> UserORM:
    return UserORM(
        id=9,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=lender_id,
        client_id=client_id,
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


def test_client_can_create_pending_deal(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post(
            "/client/me/deals",
            json={"name": "Working Capital", "value": 25_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Working Capital"
    assert payload["value"] == 25_000
    assert payload["client_id"] == 2
    assert payload["status"] == "PENDING"
    assert "industry" not in payload
    assert "client_id" not in {"name": "Working Capital", "value": 25_000}

    stored = seeded_db.execute(select(DealORM)).scalar_one()
    assert stored.client_id == 2
    assert stored.status == "PENDING"
    assert stored.name == "Working Capital"


def test_create_deal_request_does_not_require_client_id_or_industry(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post(
            "/client/me/deals",
            json={"name": "Facility A", "value": 10_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["client_id"] == 2


def test_create_deal_ignores_attempted_foreign_client_id(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.post(
            "/client/me/deals",
            json={
                "name": "Sneaky Deal",
                "value": 1_000,
                "client_id": 3,
                "industry": "retail",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_id"] == 2
    assert payload["status"] == "PENDING"

    stored = seeded_db.execute(select(DealORM)).scalar_one()
    assert stored.client_id == 2


def test_client_without_client_id_cannot_create_deal(seeded_db: Session):
    client = _override(_unlinked_client_user(), seeded_db)
    try:
        response = client.post(
            "/client/me/deals",
            json={"name": "No Client Deal", "value": 5_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert seeded_db.execute(select(DealORM)).scalars().all() == []
