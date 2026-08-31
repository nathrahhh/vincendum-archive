"""Tests for lender industry exposure API."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import lenders as lenders_routes
from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.models.position import PositionORM
from app.models.user import UserORM

_test_app = FastAPI()
_test_app.include_router(lenders_routes.router)

_TEST_TABLES = [
    LenderORM.__table__,
    PortfolioORM.__table__,
    ClientORM.__table__,
    DealORM.__table__,
    PositionORM.__table__,
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
    db_session.add_all(
        [
            LenderORM(
                id=1,
                name="Lender A",
                slug="lender-a",
                capital_base=10_000_000,
            ),
            LenderORM(
                id=2,
                name="Lender B",
                slug="lender-b",
                capital_base=10_000_000,
            ),
        ]
    )
    db_session.add_all(
        [
            PortfolioORM(
                id=1,
                name="Main",
                lender_id=1,
                capital_allocation=5_000_000,
            ),
            PortfolioORM(
                id=2,
                name="Lender B Portfolio",
                lender_id=2,
                capital_allocation=1_000_000,
            ),
        ]
    )
    db_session.add_all(
        [
            ClientORM(
                id=10,
                name="Tech Co",
                industry="Technology",
                credit_limit=1_000_000,
                lender_id=1,
                portfolio_id=1,
            ),
            ClientORM(
                id=20,
                name="Retail Co",
                industry="Retail",
                credit_limit=1_000_000,
                lender_id=2,
                portfolio_id=2,
            ),
        ]
    )
    db_session.add_all(
        [
            DealORM(
                id=100,
                client_id=10,
                name="Tech Loan",
                value=999_999,
                status="APPROVED",
            ),
            DealORM(
                id=200,
                client_id=20,
                name="Retail Loan",
                value=888_888,
                status="APPROVED",
            ),
        ]
    )
    db_session.add_all(
        [
            PositionORM(id=1, deal_id=100, value=500_000),
            PositionORM(id=2, deal_id=200, value=900_000),
        ]
    )
    db_session.add_all(
        [
            UserORM(
                id=8,
                email="admin@example.com",
                auth0_user_id="auth0|admin-a",
                role="admin",
                lender_id=1,
                client_id=None,
            ),
            UserORM(
                id=9,
                email="client@example.com",
                auth0_user_id="auth0|client",
                role="client",
                lender_id=1,
                client_id=10,
            ),
        ]
    )
    db_session.commit()
    return db_session


def _user(
    *,
    user_id: int,
    role: str,
    lender_id: int | None,
    client_id: int | None = None,
) -> UserORM:
    return UserORM(
        id=user_id,
        email=f"user-{user_id}@example.com",
        auth0_user_id=f"auth0|{user_id}",
        role=role,
        lender_id=lender_id,
        client_id=client_id,
    )


def _override(user: UserORM, db: Session) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    _test_app.dependency_overrides[get_db] = override_get_db
    _test_app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(_test_app)


def _clear_overrides() -> None:
    _test_app.dependency_overrides.pop(get_db, None)
    _test_app.dependency_overrides.pop(get_current_user, None)


def test_admin_gets_lender_industry_exposure(seeded_db: Session) -> None:
    client = _override(_user(user_id=8, role="admin", lender_id=1), seeded_db)
    try:
        response = client.get("/lenders/me/industry-exposure")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "industry": "Technology",
            "value": 500_000,
            "percentage": 100.0,
        }
    ]


def test_industry_exposure_uses_position_value_not_deal_value(
    seeded_db: Session,
) -> None:
    """PositionORM.value is outstanding exposure; DealORM.value must not be used."""
    client = _override(_user(user_id=8, role="admin", lender_id=1), seeded_db)
    try:
        response = client.get("/lenders/me/industry-exposure")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["value"] == 500_000
    assert payload[0]["value"] != 999_999


def test_industry_exposure_excludes_other_lender_positions(
    seeded_db: Session,
) -> None:
    client = _override(_user(user_id=8, role="admin", lender_id=1), seeded_db)
    try:
        response = client.get("/lenders/me/industry-exposure")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    industries = {row["industry"] for row in response.json()}
    assert "Retail" not in industries


def test_industry_exposure_empty_when_no_positions(db_session: Session) -> None:
    db_session.add(
        LenderORM(
            id=1,
            name="Lender A",
            slug="lender-a",
            capital_base=10_000_000,
        )
    )
    db_session.add(
        PortfolioORM(
            id=1,
            name="Empty",
            lender_id=1,
            capital_allocation=1_000_000,
        )
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

    client = _override(_user(user_id=8, role="admin", lender_id=1), db_session)
    try:
        response = client.get("/lenders/me/industry-exposure")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json() == []


def test_client_cannot_access_industry_exposure(seeded_db: Session) -> None:
    client = _override(
        _user(user_id=9, role="client", lender_id=1, client_id=10),
        seeded_db,
    )
    try:
        response = client.get("/lenders/me/industry-exposure")
    finally:
        _clear_overrides()

    assert response.status_code == 403
