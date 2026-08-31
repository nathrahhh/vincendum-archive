"""Tests for portfolio monitoring API routes."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.portfolio import PortfolioORM
from app.models.position import PositionORM
from app.models.user import UserORM

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
def lender_only_db(db_session: Session) -> Session:
    db_session.add(
        LenderORM(
            id=1,
            name="Lender A",
            slug="lender-a",
            capital_base=10_000_000,
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
    return db_session


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
                name="Other Lender Portfolio",
                lender_id=2,
                capital_allocation=1_000_000,
            ),
        ]
    )
    db_session.add(
        ClientORM(
            id=10,
            name="Tech Co",
            industry="Technology",
            credit_limit=1_000_000,
            lender_id=1,
            portfolio_id=1,
        )
    )
    db_session.add(
        DealORM(
            id=100,
            client_id=10,
            name="Tech Loan",
            value=500_000,
            status="APPROVED",
        )
    )
    db_session.add(
        PositionORM(
            id=1,
            deal_id=100,
            value=500_000,
        )
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
            UserORM(
                id=10,
                email="admin-b@example.com",
                auth0_user_id="auth0|admin-b",
                role="admin",
                lender_id=2,
                client_id=None,
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

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_get_portfolio_summary_success(seeded_db: Session) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        seeded_db,
    )
    try:
        response = client.get("/portfolios/1")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_id"] == 1
    assert payload["portfolio_name"] == "Main"
    assert payload["capital_allocation"] == 5_000_000
    assert payload["total_exposure"] == 500_000
    assert payload["position_count"] == 1
    assert payload["client_count"] == 1
    assert payload["utilization_pct"] == 10.0
    assert payload["industry_exposure"] == [
        {
            "industry": "Technology",
            "value": 500_000,
            "percentage": 100.0,
        }
    ]


def test_get_portfolio_not_found(seeded_db: Session) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        seeded_db,
    )
    try:
        response = client.get("/portfolios/999")
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio 999 not found"


def test_get_portfolio_cross_lender_access_returns_not_found(
    seeded_db: Session,
) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        seeded_db,
    )
    try:
        response = client.get("/portfolios/2")
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio 2 not found"


def test_client_cannot_access_portfolio_summary(seeded_db: Session) -> None:
    client = _override(
        _user(user_id=9, role="client", lender_id=1, client_id=10),
        seeded_db,
    )
    try:
        response = client.get("/portfolios/1")
    finally:
        _clear_overrides()

    assert response.status_code == 403


def test_create_portfolio_success(lender_only_db: Session) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        lender_only_db,
    )
    try:
        response = client.post(
            "/portfolios",
            json={"name": "Core Lending", "capital_allocation": 2_500_000},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Core Lending"
    assert payload["lender_id"] == 1
    assert payload["capital_allocation"] == 2_500_000
    assert payload["id"] is not None


def test_create_multiple_portfolios_for_same_lender(lender_only_db: Session) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        lender_only_db,
    )
    try:
        first = client.post(
            "/portfolios",
            json={"name": "Core", "capital_allocation": 1_000_000},
        )
        second = client.post(
            "/portfolios",
            json={"name": "Growth", "capital_allocation": 750_000},
        )
        listing = client.get("/portfolios")
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 200
    assert listing.status_code == 200
    payload = listing.json()
    assert len(payload) == 2
    assert [row["name"] for row in payload] == ["Core", "Growth"]
    assert all(row["lender_id"] == 1 for row in payload)


def test_list_portfolios_excludes_other_lenders(seeded_db: Session) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        seeded_db,
    )
    try:
        response = client.get("/portfolios")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 1
    assert payload[0]["name"] == "Main"
    assert payload[0]["lender_id"] == 1


def test_create_portfolio_rejects_negative_capital_allocation(
    lender_only_db: Session,
) -> None:
    client = _override(
        _user(user_id=8, role="admin", lender_id=1),
        lender_only_db,
    )
    try:
        response = client.post(
            "/portfolios",
            json={"name": "Invalid", "capital_allocation": -100},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422
