from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.client import ClientORM
from app.models.client_invitation import ClientInvitationORM
from app.models.lender import LenderORM
from app.models.user import UserORM
from app.services.client_invitation_service import hash_invitation_token


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
            ClientInvitationORM.__table__,
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
                ClientInvitationORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    lender_a = LenderORM(id=1, name="Lender A", slug="lender-a")
    lender_b = LenderORM(id=2, name="Lender B", slug="lender-b")
    client_a = ClientORM(
        id=10,
        name="Client A",
        industry="tech",
        credit_limit=100_000.0,
        lender_id=1,
    )
    client_b = ClientORM(
        id=20,
        name="Client B",
        industry="retail",
        credit_limit=50_000.0,
        lender_id=2,
    )
    db_session.add_all([lender_a, lender_b, client_a, client_b])
    db_session.commit()
    return db_session


def _admin_user(*, lender_id: int | None = 1) -> UserORM:
    return UserORM(
        id=1,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=lender_id,
    )


def _client_user(*, lender_id: int | None = 1) -> UserORM:
    return UserORM(
        id=2,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=lender_id,
        client_id=10,
    )


def _override_auth_and_db(user: UserORM | None, db: Session) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if user is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_invite_client_success(seeded_db: Session):
    client = _override_auth_and_db(_admin_user(), seeded_db)
    try:
        response = client.post(
            "/clients/10/invite",
            json={"email": "Invitee@Example.com"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_id"] == 10
    assert payload["email"] == "invitee@example.com"
    assert payload["status"] == "pending"
    assert "token" in payload
    assert payload["token"]
    assert payload["invitation_url"].endswith(f"/invite/{payload['token']}")
    assert "token_hash" not in payload

    stored = seeded_db.execute(
        select(ClientInvitationORM).where(ClientInvitationORM.id == payload["id"])
    ).scalar_one()
    assert stored.lender_id == 1
    assert stored.client_id == 10
    assert stored.status == "pending"
    assert stored.token_hash == hash_invitation_token(payload["token"])
    assert stored.token_hash != payload["token"]
    assert stored.expires_at is not None
    # SQLite may return naive datetimes; compare as aware UTC.
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc) + timedelta(days=6)
    assert expires_at < datetime.now(timezone.utc) + timedelta(days=8)


def test_invite_client_other_lender_returns_404(seeded_db: Session):
    client = _override_auth_and_db(_admin_user(lender_id=1), seeded_db)
    try:
        response = client.post(
            "/clients/20/invite",
            json={"email": "other@example.com"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    assert seeded_db.execute(select(ClientInvitationORM)).scalars().all() == []


def test_invite_nonexistent_client_returns_404(seeded_db: Session):
    client = _override_auth_and_db(_admin_user(), seeded_db)
    try:
        response = client.post(
            "/clients/999/invite",
            json={"email": "missing@example.com"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404


def test_invite_unauthenticated_returns_401(seeded_db: Session):
    client = _override_auth_and_db(None, seeded_db)
    try:
        response = client.post(
            "/clients/10/invite",
            json={"email": "nouser@example.com"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401


def test_invite_non_admin_returns_403(seeded_db: Session):
    client = _override_auth_and_db(_client_user(), seeded_db)
    try:
        response = client.post(
            "/clients/10/invite",
            json={"email": "forbidden@example.com"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_invite_duplicate_pending_returns_409(seeded_db: Session):
    client = _override_auth_and_db(_admin_user(), seeded_db)
    try:
        first = client.post(
            "/clients/10/invite",
            json={"email": "dup@example.com"},
        )
        second = client.post(
            "/clients/10/invite",
            json={"email": "DUP@example.com"},
        )
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 409
    assert "pending invitation" in second.json()["detail"].lower()

    invitations = seeded_db.execute(select(ClientInvitationORM)).scalars().all()
    assert len(invitations) == 1
    assert invitations[0].email == "dup@example.com"
