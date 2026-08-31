from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import (
    AuthenticatedAuth0Identity,
    get_authenticated_auth0_identity,
)
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
            UserORM.__table__,
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
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    lender = LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000)
    client = ClientORM(
        id=10,
        name="Client A",
        industry="tech",
        credit_limit=100_000.0,
        lender_id=1,
    )
    db_session.add_all([lender, client])
    db_session.commit()
    return db_session


def _identity(*, email: str = "invitee@example.com") -> AuthenticatedAuth0Identity:
    return AuthenticatedAuth0Identity(
        auth0_user_id="auth0|invitee",
        email=email,
    )


def _override(
    identity: AuthenticatedAuth0Identity | None,
    db: Session,
) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if identity is None:
        app.dependency_overrides.pop(get_authenticated_auth0_identity, None)
    else:
        app.dependency_overrides[get_authenticated_auth0_identity] = (
            lambda: identity
        )
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_authenticated_auth0_identity, None)


def _add_invitation(
    db: Session,
    *,
    raw_token: str,
    email: str = "invitee@example.com",
    status: str = "pending",
    expires_at: datetime | None = None,
) -> ClientInvitationORM:
    invitation = ClientInvitationORM(
        lender_id=1,
        client_id=10,
        email=email,
        token_hash=hash_invitation_token(raw_token),
        status=status,
        expires_at=expires_at
        or (datetime.now(timezone.utc) + timedelta(days=7)),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def test_accept_invitation_creates_client_user(seeded_db: Session):
    raw_token = "accept-success-token"
    _add_invitation(seeded_db, raw_token=raw_token)

    client = _override(_identity(), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": raw_token},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "invitation_id": payload["invitation_id"],
        "client_id": 10,
        "client_name": "Client A",
        "status": "accepted",
        "role": "client",
    }

    user = seeded_db.execute(
        select(UserORM).where(UserORM.auth0_user_id == "auth0|invitee")
    ).scalar_one()
    assert user.role == "client"
    assert user.client_id == 10
    assert user.lender_id == 1
    assert user.email == "invitee@example.com"


def test_accept_invitation_updates_existing_user(seeded_db: Session):
    raw_token = "accept-existing-token"
    _add_invitation(seeded_db, raw_token=raw_token)
    existing = UserORM(
        email="invitee@example.com",
        auth0_user_id="auth0|invitee",
        role="admin",
        lender_id=None,
        client_id=None,
    )
    seeded_db.add(existing)
    seeded_db.commit()

    client = _override(_identity(), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": raw_token},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    seeded_db.refresh(existing)
    assert existing.role == "client"
    assert existing.client_id == 10
    assert existing.lender_id == 1


def test_accept_invitation_invalid_token_returns_404(seeded_db: Session):
    client = _override(_identity(), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": "does-not-exist"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert seeded_db.execute(select(UserORM)).scalars().all() == []


def test_accept_invitation_expired_returns_410(seeded_db: Session):
    raw_token = "expired-token"
    _add_invitation(
        seeded_db,
        raw_token=raw_token,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    client = _override(_identity(), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": raw_token},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 410


def test_accept_invitation_already_accepted_returns_409(seeded_db: Session):
    raw_token = "already-accepted-token"
    _add_invitation(seeded_db, raw_token=raw_token, status="accepted")

    client = _override(_identity(), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": raw_token},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 409


def test_accept_invitation_email_mismatch_returns_403(seeded_db: Session):
    raw_token = "email-mismatch-token"
    _add_invitation(seeded_db, raw_token=raw_token, email="invited@example.com")

    client = _override(_identity(email="other@example.com"), seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": raw_token},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert "email" in response.json()["detail"].lower()
    assert seeded_db.execute(select(UserORM)).scalars().all() == []


def test_accept_invitation_unauthenticated_returns_401(seeded_db: Session):
    client = _override(None, seeded_db)
    try:
        response = client.post(
            "/client-invitations/accept",
            json={"token": "any-token"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401
