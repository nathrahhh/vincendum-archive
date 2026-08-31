from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.audit_log import AuditLogORM
from app.models.lender import LenderORM
from app.models.user import UserORM


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw) -> str:
    return "JSON"


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
            UserORM.__table__,
            AuditLogORM.__table__,
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
                AuditLogORM.__table__,
                UserORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    lender_a = LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000)
    lender_b = LenderORM(id=2, name="Lender B", slug="lender-b", capital_base=10_000_000)
    admin_user = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    client_user = UserORM(
        id=9,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=1,
        client_id=2,
    )
    audit_logs = [
        AuditLogORM(
            lender_id=1,
            user_id=8,
            action="deal.approved",
            resource_type="deal",
            resource_id=1,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
        AuditLogORM(
            lender_id=1,
            user_id=8,
            action="client_financial.approved",
            resource_type="client_financial",
            resource_id=2,
            created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        ),
        AuditLogORM(
            lender_id=1,
            user_id=8,
            action="deal.approved",
            resource_type="deal",
            resource_id=3,
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
        AuditLogORM(
            lender_id=2,
            user_id=8,
            action="deal.approved",
            resource_type="deal",
            resource_id=99,
            created_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all([lender_a, lender_b, admin_user, client_user, *audit_logs])
    db_session.commit()
    return db_session


def _admin_user() -> UserORM:
    return UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=1,
        client_id=None,
    )


def _client_user() -> UserORM:
    return UserORM(
        id=9,
        email="client@example.com",
        auth0_user_id="auth0|client",
        role="client",
        lender_id=1,
        client_id=2,
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


def test_admin_can_retrieve_own_lender_audit_logs(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/audit-logs")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert all(row["lender_id"] == 1 for row in payload)
    assert {row["resource_id"] for row in payload} == {1, 2, 3}


def test_audit_logs_are_newest_first(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/audit-logs")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    resource_ids = [row["resource_id"] for row in response.json()]
    assert resource_ids == [2, 3, 1]


def test_audit_logs_respect_limit(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/audit-logs?limit=2")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_client_cannot_access_audit_logs(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.get("/audit-logs")
    finally:
        _clear_overrides()

    assert response.status_code == 403


def test_other_lender_audit_logs_are_not_exposed(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/audit-logs")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert all(row["resource_id"] != 99 for row in response.json())
