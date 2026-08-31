"""Tests for lender onboarding API."""

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
from app.models.user import UserORM

_TEST_TABLES = [
    LenderORM.__table__,
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


def _new_admin_user(
    *,
    user_id: int = 8,
    lender_id: int | None = None,
) -> UserORM:
    return UserORM(
        id=user_id,
        email=f"admin{user_id}@example.com",
        auth0_user_id=f"auth0|admin-{user_id}",
        role="admin",
        lender_id=lender_id,
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


def test_onboard_lender_success(db_session: Session) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "ABC Capital", "capital_base": 12_500_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "ABC Capital"
    assert payload["slug"] == "abc-capital"
    assert payload["capital_base"] == 12_500_000

    lender = db_session.execute(select(LenderORM)).scalar_one()
    assert lender.name == "ABC Capital"
    assert lender.capital_base == 12_500_000

    db_session.refresh(admin)
    assert admin.lender_id == lender.id


def test_onboard_lender_stores_supplied_capital_base(db_session: Session) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "Growth Lending", "capital_base": 5_000_000.5},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    lender = db_session.execute(select(LenderORM)).scalar_one()
    assert lender.capital_base == 5_000_000.5


def test_onboard_lender_rejects_missing_capital_base(db_session: Session) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "ABC Capital"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


def test_onboard_lender_rejects_zero_capital_base(db_session: Session) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "ABC Capital", "capital_base": 0},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


def test_onboard_lender_rejects_negative_capital_base(
    db_session: Session,
) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "ABC Capital", "capital_base": -1000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


def test_onboard_lender_rejects_empty_name(db_session: Session) -> None:
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "   ", "capital_base": 1_000_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "Lender name is required"


def test_user_with_lender_cannot_onboard_again(db_session: Session) -> None:
    db_session.add(
        LenderORM(
            id=1,
            name="Existing Lender",
            slug="existing-lender",
            capital_base=10_000_000,
        )
    )
    admin = _new_admin_user(lender_id=1)
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "Another Lender", "capital_base": 1_000_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "User has already completed lender onboarding"


def test_onboard_generates_unique_slug_on_collision(db_session: Session) -> None:
    db_session.add(
        LenderORM(
            id=1,
            name="ABC Capital",
            slug="abc-capital",
            capital_base=10_000_000,
        )
    )
    admin = _new_admin_user()
    db_session.add(admin)
    db_session.commit()

    client = _override(admin, db_session)
    try:
        response = client.post(
            "/lenders/onboard",
            json={"name": "ABC Capital", "capital_base": 2_000_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["slug"] == "abc-capital-2"
