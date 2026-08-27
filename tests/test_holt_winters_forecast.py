"""Unit tests for the Holt-Winters forecasting model."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.forecasting.cache_keys import holt_winters_forecast_cache_key
from app.services.forecasting.deterministic import FORECAST_MONTHS, _add_months
from app.services.forecasting.holt_winters import (
    MIN_SEASONAL_OBSERVATIONS,
    SEASONAL_PERIOD,
    UNAVAILABLE_INSUFFICIENT_HISTORY,
    UNAVAILABLE_NON_CONSECUTIVE_MONTHS,
    build_holt_winters_forecast,
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
    # Distinct monthly revenues so incorrect seasonal periods would be obvious.
    return [
        _row(
            _add_months(start, offset),
            float(20_000 + offset * 400 + ((offset % 12) + 1) * 2_000),
        )
        for offset in range(months)
    ]


def test_holt_winters_cache_key_includes_client_id() -> None:
    assert holt_winters_forecast_cache_key(7) == "forecast:holt_winters:7"


def test_holt_winters_produces_six_month_forecast_with_valid_history() -> None:
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
        ) as mock_set,
    ):
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result["client_id"] == 7
    assert result["model"] == "holt_winters"
    assert result["unavailable_reason"] is None
    assert len(result["historical"]) == 24
    assert result["historical"][0]["month"] == "2024-01"
    assert result["historical"][-1]["month"] == "2025-12"
    assert result["historical"][0]["revenue"] == history[0]["revenue"]

    assert len(result["forecast"]) == FORECAST_MONTHS
    assert [point["month"] for point in result["forecast"]] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]
    assert all(isinstance(point["revenue"], float) for point in result["forecast"])
    mock_set.assert_called_once()


def test_holt_winters_uses_twelve_month_seasonality_with_enough_history() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=24)
    assert len(history) >= MIN_SEASONAL_OBSERVATIONS

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
            "app.services.forecasting.holt_winters.ExponentialSmoothing",
        ) as mock_model_cls,
        patch(
            "app.services.forecasting.holt_winters.cache_set_json",
            return_value=True,
        ),
    ):
        fitted = MagicMock()
        fitted.forecast.return_value = MagicMock(
            iloc=[200.0, 201.0, 202.0, 203.0, 204.0, 205.0]
        )
        mock_model_cls.return_value.fit.return_value = fitted
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result["model"] == "holt_winters"
    assert len(result["forecast"]) == FORECAST_MONTHS
    kwargs = mock_model_cls.call_args.kwargs
    assert kwargs["trend"] == "add"
    assert kwargs["seasonal"] == "add"
    assert kwargs["seasonal_periods"] == SEASONAL_PERIOD


def test_holt_winters_falls_back_to_non_seasonal_holt_without_fabricating_seasonality() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2025, 1, 1), months=12)
    assert len(history) < MIN_SEASONAL_OBSERVATIONS

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
            "app.services.forecasting.holt_winters.ExponentialSmoothing",
        ) as mock_model_cls,
        patch(
            "app.services.forecasting.holt_winters.cache_set_json",
            return_value=True,
        ),
    ):
        fitted = MagicMock()
        fitted.forecast.return_value = MagicMock(
            iloc=[110.0, 111.0, 112.0, 113.0, 114.0, 115.0]
        )
        mock_model_cls.return_value.fit.return_value = fitted
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result["model"] == "holt_winters"
    assert result["unavailable_reason"] is None
    assert len(result["forecast"]) == FORECAST_MONTHS
    kwargs = mock_model_cls.call_args.kwargs
    assert kwargs["trend"] == "add"
    assert kwargs["seasonal"] is None
    assert kwargs["seasonal_periods"] is None


def test_holt_winters_insufficient_history_does_not_fabricate_forecast() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2026, 1, 1), months=2)

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
        ) as mock_set,
    ):
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result["model"] == "holt_winters"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_INSUFFICIENT_HISTORY
    assert len(result["historical"]) == 2
    mock_set.assert_not_called()


def test_holt_winters_missing_calendar_months_is_unavailable() -> None:
    db = MagicMock()
    history = (
        _consecutive_history(start=date(2024, 1, 1), months=12)
        + _consecutive_history(start=date(2025, 2, 1), months=12)
    )

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
        ) as mock_set,
    ):
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result["model"] == "holt_winters"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_NON_CONSECUTIVE_MONTHS
    mock_set.assert_not_called()


def test_holt_winters_cache_hit_skips_recalculation() -> None:
    db = MagicMock()
    cached = {
        "client_id": 7,
        "model": "holt_winters",
        "historical": [{"month": "2025-12", "revenue": 24_000.0}],
        "forecast": [{"month": "2026-01", "revenue": 24_400.0}],
        "unavailable_reason": None,
    }

    with (
        patch(
            "app.services.forecasting.holt_winters.cache_get_json",
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.forecasting.holt_winters._compute_holt_winters_forecast",
        ) as mock_compute,
        patch(
            "app.services.forecasting.holt_winters.cache_set_json",
        ) as mock_set,
    ):
        result = build_holt_winters_forecast(db=db, client_id=7)

    assert result == cached
    mock_get.assert_called_once()
    mock_compute.assert_not_called()
    mock_set.assert_not_called()
    db.execute.assert_not_called()
