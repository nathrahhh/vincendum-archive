"""Unit and API tests for statistical forecast backtesting."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from unittest.mock import MagicMock, patch

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
from app.models.lender import LenderORM
from app.models.schemas import ForecastBacktestResponse
from app.models.user import UserORM
from app.services.forecasting.backtest import (
    HOLDOUT_MONTHS,
    STATISTICAL_BACKTEST_MODELS,
    UNAVAILABLE_INSUFFICIENT_HISTORY,
    build_forecast_backtest,
)
from app.services.forecasting.shared import _add_months
from app.services.forecasting.naive import forecast_naive_from_history


def _row(month: date, revenue: float) -> dict:
    return {
        "month": month,
        "revenue": revenue,
        "cogs": 0.0,
        "opex": 0.0,
        "gross_profit": revenue,
        "cash_balance": 0.0,
    }


def _consecutive_history(*, start: date, months: int, base: float = 10_000.0) -> list[dict]:
    return [
        _row(_add_months(start, offset), float(base + offset * 100))
        for offset in range(months)
    ]


def test_naive_backtest_produces_valid_mae() -> None:
    db = MagicMock()
    # Flat train revenue then a step change in the holdout so naive MAE is known.
    history = [
        *_consecutive_history(start=date(2024, 1, 1), months=12, base=100_000.0),
    ]
    # Override holdout months to distinct values for an exact MAE.
    for index in range(HOLDOUT_MONTHS):
        history[-(HOLDOUT_MONTHS - index)]["revenue"] = float(130_000 + index)

    with patch(
        "app.services.forecasting.backtest._fetch_client_financials",
        return_value=history,
    ):
        result = build_forecast_backtest(db=db, client_id=7)

    by_model = {row["model"]: row for row in result["results"]}
    naive = by_model["naive"]
    assert naive["available"] is True
    assert isinstance(naive["mae"], float)
    # Train ends at month index 5 (2024-06) with revenue 100000 + 5*100 = 100500
    train_latest = 100_000.0 + (12 - HOLDOUT_MONTHS - 1) * 100
    expected_mae = round(
        sum(abs(train_latest - float(130_000 + index)) for index in range(HOLDOUT_MONTHS))
        / HOLDOUT_MONTHS,
        2,
    )
    assert naive["mae"] == expected_mae


def test_best_model_is_lowest_mae() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2023, 1, 1), months=24)

    # Holdout months are 2024-07 .. 2024-12 with revenues 11800..12300.
    holdout_start = date(2024, 7, 1)
    actuals = [11_800.0 + index * 100 for index in range(6)]

    def _points(revenues: list[float]) -> list[dict]:
        return [
            {
                "month": _add_months(holdout_start, offset).strftime("%Y-%m"),
                "revenue": revenues[offset],
            }
            for offset in range(len(revenues))
        ]

    with (
        patch(
            "app.services.forecasting.backtest._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.backtest.forecast_naive_from_history",
            return_value=(_points([actual + 500 for actual in actuals]), None),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_seasonal_naive_from_history",
            return_value=(_points([actual + 200 for actual in actuals]), None),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_ets_from_history",
            return_value=(_points(actuals), None),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_holt_winters_from_history",
            return_value=(_points([actual + 50 for actual in actuals]), None),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_prophet_from_history",
            return_value=(_points([actual + 100 for actual in actuals]), None),
        ),
    ):
        result = build_forecast_backtest(db=db, client_id=7)

    assert result["best_model"] == "ets"
    by_model = {row["model"]: row for row in result["results"]}
    assert by_model["ets"]["mae"] == 0.0
    assert [row["model"] for row in result["results"]] == list(STATISTICAL_BACKTEST_MODELS)
    assert all(row["available"] for row in result["results"])


def test_all_five_models_evaluated_with_sufficient_history() -> None:
    db = MagicMock()
    # 24 months → 18 train / 6 holdout: enough for seasonal_naive (12) and others.
    history = _consecutive_history(start=date(2023, 1, 1), months=24)

    with patch(
        "app.services.forecasting.backtest._fetch_client_financials",
        return_value=history,
    ):
        result = build_forecast_backtest(db=db, client_id=7)

    assert result["client_id"] == 7
    assert result["metric"] == "mae"
    assert result["holdout_months"] == HOLDOUT_MONTHS
    assert len(result["results"]) == 5
    assert {row["model"] for row in result["results"]} == set(STATISTICAL_BACKTEST_MODELS)
    assert all(row["available"] for row in result["results"])
    assert result["best_model"] in STATISTICAL_BACKTEST_MODELS
    ForecastBacktestResponse.model_validate(result)


def test_insufficient_history_marks_all_models_unavailable() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2026, 1, 1), months=HOLDOUT_MONTHS)

    with patch(
        "app.services.forecasting.backtest._fetch_client_financials",
        return_value=history,
    ):
        result = build_forecast_backtest(db=db, client_id=7)

    assert result["best_model"] is None
    assert all(row["available"] is False for row in result["results"])
    assert all(
        row["unavailable_reason"] == UNAVAILABLE_INSUFFICIENT_HISTORY
        for row in result["results"]
    )


def test_unavailable_model_does_not_fail_entire_backtest() -> None:
    db = MagicMock()
    # 12 months → 6 train / 6 holdout: naive/ets/hw/prophet OK; seasonal_naive needs 12 train.
    history = _consecutive_history(start=date(2025, 1, 1), months=12)

    with patch(
        "app.services.forecasting.backtest._fetch_client_financials",
        return_value=history,
    ):
        result = build_forecast_backtest(db=db, client_id=7)

    by_model = {row["model"]: row for row in result["results"]}
    assert by_model["naive"]["available"] is True
    assert by_model["seasonal_naive"]["available"] is False
    assert by_model["seasonal_naive"]["unavailable_reason"] == UNAVAILABLE_INSUFFICIENT_HISTORY
    assert result["best_model"] is not None
    assert result["best_model"] != "seasonal_naive"


def test_backtest_preserves_chronological_order_without_shuffle() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=18)
    captured: list[list[tuple[date, float]]] = []

    def _capture_naive(train, *, horizon: int):
        captured.append(list(train))
        return forecast_naive_from_history(train, horizon=horizon)

    with (
        patch(
            "app.services.forecasting.backtest._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.backtest.forecast_naive_from_history",
            side_effect=_capture_naive,
        ),
        patch(
            "app.services.forecasting.backtest.forecast_seasonal_naive_from_history",
            return_value=([], UNAVAILABLE_INSUFFICIENT_HISTORY),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_ets_from_history",
            return_value=([], UNAVAILABLE_INSUFFICIENT_HISTORY),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_holt_winters_from_history",
            return_value=([], UNAVAILABLE_INSUFFICIENT_HISTORY),
        ),
        patch(
            "app.services.forecasting.backtest.forecast_prophet_from_history",
            return_value=([], UNAVAILABLE_INSUFFICIENT_HISTORY),
        ),
    ):
        build_forecast_backtest(db=db, client_id=7)

    assert len(captured) == 1
    train = captured[0]
    assert [month for month, _ in train] == [
        _add_months(date(2024, 1, 1), offset) for offset in range(12)
    ]
    assert train == sorted(train, key=lambda item: item[0])


# --- API authorization / wiring ---


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
    lender = LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000)
    client_2 = ClientORM(
        id=2,
        name="Client Two",
        industry="tech",
        credit_limit=100_000.0,
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
    db_session.add_all([lender, client_2, client_user, admin_user])
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


def test_client_me_forecast_backtest_uses_authenticated_client_id(seeded_db: Session) -> None:
    mock_response = ForecastBacktestResponse(
        client_id=2,
        metric="mae",
        holdout_months=6,
        best_model="naive",
        results=[
            {
                "model": "naive",
                "mae": 1.0,
                "available": True,
                "unavailable_reason": None,
            }
        ],
    )
    client = _override(_client_user(), seeded_db)
    try:
        with patch(
            "app.api.routes.forecast.build_forecast_backtest",
            return_value=mock_response.model_dump(),
        ) as mock_backtest:
            response = client.get("/client/me/forecast/backtest")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_id"] == 2
    assert payload["metric"] == "mae"
    mock_backtest.assert_called_once()
    assert mock_backtest.call_args.kwargs["client_id"] == 2


def test_admin_forecast_backtest_endpoint_returns_schema(seeded_db: Session) -> None:
    mock_response = {
        "client_id": 2,
        "metric": "mae",
        "holdout_months": 6,
        "best_model": "ets",
        "results": [
            {
                "model": model,
                "mae": float(index),
                "available": True,
                "unavailable_reason": None,
            }
            for index, model in enumerate(STATISTICAL_BACKTEST_MODELS)
        ],
    }
    client = _override(_admin_user(), seeded_db)
    try:
        with patch(
            "app.api.routes.forecast.build_forecast_backtest",
            return_value=mock_response,
        ):
            response = client.get("/clients/2/forecast/backtest")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    ForecastBacktestResponse.model_validate(payload)
    assert payload["best_model"] == "ets"
    assert len(payload["results"]) == 5


def test_admin_forecast_backtest_is_admin_protected(seeded_db: Session) -> None:
    client = _override(_client_user(), seeded_db)
    try:
        response = client.get("/clients/2/forecast/backtest")
    finally:
        _clear_overrides()

    assert response.status_code in {401, 403}
