"""Tests for lender capital-base update API."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.models.user import UserORM

_TEST_TABLES = [
    LenderORM.__table__,
    PortfolioORM.__table__,
    UserORM.__table__,
]


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=_TEST_TABLES)
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
        Base.metadata.drop_all(bind=engine, tables=list(reversed(_TEST_TABLES)))


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    db_session.add(
        LenderORM(
            id=1,
            name="Lender A",
            slug="lender-a",
            capital_base=1_000_000,
        )
    )
    db_session.add_all(
        [
            PortfolioORM(
                id=1,
                name="Portfolio A",
                lender_id=1,
                capital_allocation=400_000,
            ),
            PortfolioORM(
                id=2,
                name="Portfolio B",
                lender_id=1,
                capital_allocation=300_000,
            ),
        ]
    )
    db_session.add(
        UserORM(
            id=8,
            email="admin@example.com",
            auth0_user_id="auth0|admin-a",
            role="admin",
            lender_id=1,
            client_id=None,
        )
    )
    db_session.commit()
    return db_session


def _override(user: UserORM, db: Session) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_patch_lender_capital_base_succeeds_when_allocations_fit(
    seeded_db: Session,
) -> None:
    admin = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin-a",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    client = _override(admin, seeded_db)
    try:
        response = client.patch(
            "/lenders/me/capital-base",
            json={"capital_base": 800_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["capital_base"] == 800_000

    lender = seeded_db.execute(
        select(LenderORM).where(LenderORM.id == 1)
    ).scalar_one()
    assert lender.capital_base == 800_000


def test_patch_lender_capital_base_succeeds_when_increasing(
    seeded_db: Session,
) -> None:
    admin = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin-a",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    client = _override(admin, seeded_db)
    try:
        response = client.patch(
            "/lenders/me/capital-base",
            json={"capital_base": 2_000_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["capital_base"] == 2_000_000


def test_patch_lender_capital_base_fails_below_existing_allocations(
    seeded_db: Session,
) -> None:
    admin = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin-a",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    client = _override(admin, seeded_db)
    try:
        response = client.patch(
            "/lenders/me/capital-base",
            json={"capital_base": 600_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400
    assert "cannot be lower than total portfolio allocations" in response.json()["detail"]


def test_patch_lender_capital_base_rejects_zero(seeded_db: Session) -> None:
    admin = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin-a",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    client = _override(admin, seeded_db)
    try:
        response = client.patch(
            "/lenders/me/capital-base",
            json={"capital_base": 0},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422
