"""Schema conformance for statistical (revenue-only) forecasting models."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from app.models.schemas import ForecastRevenuePoint, StatisticalForecastResponse
from app.services.forecasting.shared import FORECAST_MONTHS, _add_months
from app.services.forecasting.ets import build_ets_forecast
from app.services.forecasting.holt_winters import build_holt_winters_forecast
from app.services.forecasting.naive import build_naive_forecast
from app.services.forecasting.prophet import build_prophet_forecast
from app.services.forecasting.seasonal_naive import (
    UNAVAILABLE_INSUFFICIENT_HISTORY,
    build_seasonal_naive_forecast,
)


def _row(month: date, revenue: float) -> dict:
    return {
        "month": month,
        "revenue": revenue,
        "cogs": 0.0,
        "opex": 0.0,
        "gross_profit": revenue,
        "cash_balance": 0.0,
    }


def _consecutive_history(*, start: date, months: int) -> list[dict]:
    return [
        _row(_add_months(start, offset), float(10_000 + offset * 250))
        for offset in range(months)
    ]


def _assert_revenue_only_points(points: list[dict]) -> None:
    for point in points:
        assert set(point.keys()) == {"month", "revenue"}
        assert isinstance(point["month"], str)
        assert isinstance(point["revenue"], float)
        assert "cogs" not in point
        assert "opex" not in point
        assert "cash_balance" not in point
        assert "lower_bound" not in point
        assert "upper_bound" not in point


def _assert_statistical_shape(result: dict, *, expected_model: str) -> StatisticalForecastResponse:
    parsed = StatisticalForecastResponse.model_validate(result)
    assert parsed.model == expected_model
    _assert_revenue_only_points(result["historical"])
    _assert_revenue_only_points(result["forecast"])
    assert "assumptions" not in result
    assert "alerts" not in result
    return parsed


def test_naive_conforms_to_statistical_forecast_schema() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2026, 1, 1), months=3)

    with (
        patch("app.services.forecasting.naive.cache_get_json", return_value=None),
        patch(
            "app.services.forecasting.naive._fetch_client_financials",
            return_value=history,
        ),
        patch("app.services.forecasting.naive.cache_set_json", return_value=True),
    ):
        result = build_naive_forecast(db=db, client_id=7)

    parsed = _assert_statistical_shape(result, expected_model="naive")
    assert parsed.unavailable_reason is None
    assert len(parsed.forecast) == FORECAST_MONTHS


def test_seasonal_naive_conforms_and_preserves_unavailable_reason() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2026, 1, 1), months=11)

    with (
        patch(
            "app.services.forecasting.seasonal_naive.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.seasonal_naive._fetch_client_financials",
            return_value=history,
        ),
        patch("app.services.forecasting.seasonal_naive.cache_set_json"),
    ):
        result = build_seasonal_naive_forecast(db=db, client_id=7)

    parsed = _assert_statistical_shape(result, expected_model="seasonal_naive")
    assert parsed.forecast == []
    assert parsed.unavailable_reason == UNAVAILABLE_INSUFFICIENT_HISTORY


def test_ets_conforms_to_statistical_forecast_schema() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=24)

    with (
        patch("app.services.forecasting.ets.cache_get_json", return_value=None),
        patch(
            "app.services.forecasting.ets._fetch_client_financials",
            return_value=history,
        ),
        patch("app.services.forecasting.ets.cache_set_json", return_value=True),
    ):
        result = build_ets_forecast(db=db, client_id=7)

    parsed = _assert_statistical_shape(result, expected_model="ets")
    assert parsed.unavailable_reason is None
    assert len(parsed.forecast) == FORECAST_MONTHS


def test_holt_winters_conforms_to_statistical_forecast_schema() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=24)

    with (
        patch(
            "app.services.forecasting.holt_winters.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.holt_winters._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.holt_winters.cache_set_json",
            return_value=True,
        ),
    ):
        result = build_holt_winters_forecast(db=db, client_id=7)

    parsed = _assert_statistical_shape(result, expected_model="holt_winters")
    assert parsed.unavailable_reason is None
    assert len(parsed.forecast) == FORECAST_MONTHS


def test_prophet_returns_revenue_only_without_uncertainty_bounds() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=18)

    future_ds = pd.to_datetime(
        [_add_months(date(2025, 6, 1), offset) for offset in range(1, FORECAST_MONTHS + 1)]
    )
    prediction = pd.DataFrame(
        {
            "ds": list(pd.to_datetime([row["month"] for row in history])) + list(future_ds),
            "yhat": [float(i) for i in range(18 + FORECAST_MONTHS)],
            "yhat_lower": [0.0] * (18 + FORECAST_MONTHS),
            "yhat_upper": [999.0] * (18 + FORECAST_MONTHS),
        }
    )

    mock_model = MagicMock()
    mock_model.make_future_dataframe.return_value = prediction[["ds"]]
    mock_model.predict.return_value = prediction

    with (
        patch("app.services.forecasting.prophet.cache_get_json", return_value=None),
        patch(
            "app.services.forecasting.prophet._fetch_client_financials",
            return_value=history,
        ),
        patch("app.services.forecasting.prophet.Prophet", return_value=mock_model),
        patch("app.services.forecasting.prophet.cache_set_json", return_value=True),
    ):
        result = build_prophet_forecast(db=db, client_id=7)

    parsed = _assert_statistical_shape(result, expected_model="prophet")
    assert parsed.unavailable_reason is None
    assert len(parsed.forecast) == FORECAST_MONTHS
    assert all("lower_bound" not in point for point in result["forecast"])
    assert all("upper_bound" not in point for point in result["forecast"])


def test_forecast_revenue_point_exposes_only_month_and_revenue() -> None:
    point = ForecastRevenuePoint.model_validate(
        {"month": "2026-01", "revenue": 1.0, "cogs": 99.0, "lower_bound": 0.5}
    )
    assert point.model_dump() == {"month": "2026-01", "revenue": 1.0}
