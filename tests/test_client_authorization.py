from collections.abc import Generator
from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.position import PositionORM
from app.models.schemas import DeterministicForecastResponse
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
            DealORM.__table__,
            PositionORM.__table__,
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
                PositionORM.__table__,
                DealORM.__table__,
                ClientFinancialORM.__table__,
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    lender = LenderORM(id=1, name="Lender A")
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
    admin_user = UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=1,
        client_id=None,
    )
    financials = [
        ClientFinancialORM(
            client_id=2,
            month=date(2024, 1, 1),
            revenue=10_000.0,
            cogs=4_000.0,
            gross_profit=6_000.0,
            opex=2_000.0,
            cash_balance=5_000.0,
        ),
        ClientFinancialORM(
            client_id=3,
            month=date(2024, 1, 1),
            revenue=99_000.0,
            cogs=1_000.0,
            gross_profit=98_000.0,
            opex=1_000.0,
            cash_balance=50_000.0,
        ),
    ]
    deals = [
        DealORM(
            client_id=2,
            name="Client 2 Deal",
            value=1_000.0,
            industry="tech",
            status="PENDING",
        ),
        DealORM(
            client_id=3,
            name="Client 3 Deal",
            value=9_000.0,
            industry="retail",
            status="PENDING",
        ),
    ]
    db_session.add_all(
        [lender, client_2, client_3, client_user, admin_user, *financials, *deals]
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


def _admin_user() -> UserORM:
    return UserORM(
        id=8,
        email="admin@example.com",
        auth0_user_id="auth0|admin",
        role="admin",
        lender_id=1,
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


def test_client_me_returns_own_client(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.get("/client/me")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 2
    assert payload["name"] == "Client Two"


def test_client_me_financials_only_own_records(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.get("/client/me/financials")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_id"] == 2
    assert len(payload["historical"]) == 1
    assert all(row["client_id"] == 2 for row in payload["historical"])


def test_client_me_deals_only_own_records(seeded_db: Session):
    client = _override(_client_user(), seeded_db)
    try:
        response = client.get("/client/me/deals")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["client_id"] == 2
    assert payload[0]["name"] == "Client 2 Deal"


def test_client_me_forecast_uses_own_client_id(seeded_db: Session):
    mock_response = DeterministicForecastResponse(
        client_id=2,
        model="deterministic",
        assumptions={},
        historical=[],
        forecast=[],
        alerts={},
    )
    client = _override(_client_user(), seeded_db)
    try:
        with patch(
            "app.api.routes.forecast.build_deterministic_forecast",
            return_value=mock_response,
        ) as mock_forecast:
            response = client.get("/client/me/forecast")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["client_id"] == 2
    mock_forecast.assert_called_once()
    assert mock_forecast.call_args.kwargs["client_id"] == 2


def test_client_me_endpoints_have_no_client_id_path_param():
    paths = app.openapi()["paths"]
    assert "/client/me" in paths
    assert "/client/me/financials" in paths
    assert "/client/me/forecast" in paths
    assert "/client/me/deals" in paths
    assert "/client/me/{client_id}" not in paths


def test_admin_client_detail_still_works(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/clients/2")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["id"] == 2


def test_admin_list_deals_still_works(seeded_db: Session):
    client = _override(_admin_user(), seeded_db)
    try:
        response = client.get("/deals")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert {row["client_id"] for row in response.json()} == {2, 3}
