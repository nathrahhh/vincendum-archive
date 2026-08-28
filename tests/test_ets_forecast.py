"""Unit tests for the ETS forecasting model."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.forecasting.cache_keys import ets_forecast_cache_key
from app.services.forecasting.shared import FORECAST_MONTHS, _add_months
from app.services.forecasting.ets import (
    MIN_SEASONAL_OBSERVATIONS,
    UNAVAILABLE_INSUFFICIENT_HISTORY,
    UNAVAILABLE_NON_CONSECUTIVE_MONTHS,
    build_ets_forecast,
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
    # Distinct monthly revenues so incorrect offsets would be obvious.
    return [
        _row(
            _add_months(start, offset),
            float(10_000 + offset * 500 + ((offset % 12) + 1) * 1_000),
        )
        for offset in range(months)
    ]


def test_ets_cache_key_includes_client_id() -> None:
    assert ets_forecast_cache_key(7) == "forecast:ets:7"


def test_ets_produces_six_month_forecast_with_valid_history() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2024, 1, 1), months=24)

    with (
        patch(
            "app.services.forecasting.ets.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.ets._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.ets.cache_set_json",
            return_value=True,
        ) as mock_set,
    ):
        result = build_ets_forecast(db=db, client_id=7)

    assert result["client_id"] == 7
    assert result["model"] == "ets"
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


def test_ets_uses_non_seasonal_config_when_history_below_two_cycles() -> None:
    db = MagicMock()
    # Enough for trend, not enough for seasonal heuristic (needs 24).
    history = _consecutive_history(start=date(2025, 1, 1), months=12)
    assert len(history) < MIN_SEASONAL_OBSERVATIONS

    with (
        patch(
            "app.services.forecasting.ets.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.ets._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.ets.ETSModel",
        ) as mock_model_cls,
        patch(
            "app.services.forecasting.ets.cache_set_json",
            return_value=True,
        ),
    ):
        fitted = MagicMock()
        fitted.forecast.return_value = MagicMock(
            iloc=[100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
        )
        mock_model_cls.return_value.fit.return_value = fitted
        result = build_ets_forecast(db=db, client_id=7)

    assert result["model"] == "ets"
    assert len(result["forecast"]) == FORECAST_MONTHS
    kwargs = mock_model_cls.call_args.kwargs
    assert kwargs["seasonal"] is None
    assert kwargs["seasonal_periods"] is None
    assert kwargs["error"] == "add"
    assert kwargs["trend"] == "add"


def test_ets_insufficient_history_does_not_fabricate_forecast() -> None:
    db = MagicMock()
    history = _consecutive_history(start=date(2026, 1, 1), months=2)

    with (
        patch(
            "app.services.forecasting.ets.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.ets._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.ets.cache_set_json",
        ) as mock_set,
    ):
        result = build_ets_forecast(db=db, client_id=7)

    assert result["model"] == "ets"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_INSUFFICIENT_HISTORY
    assert len(result["historical"]) == 2
    mock_set.assert_not_called()


def test_ets_missing_calendar_months_is_unavailable() -> None:
    db = MagicMock()
    history = (
        _consecutive_history(start=date(2024, 1, 1), months=12)
        + _consecutive_history(start=date(2025, 2, 1), months=12)
    )

    with (
        patch(
            "app.services.forecasting.ets.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.ets._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.ets.cache_set_json",
        ) as mock_set,
    ):
        result = build_ets_forecast(db=db, client_id=7)

    assert result["model"] == "ets"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_NON_CONSECUTIVE_MONTHS
    mock_set.assert_not_called()


def test_ets_cache_hit_skips_recalculation() -> None:
    db = MagicMock()
    cached = {
        "client_id": 7,
        "model": "ets",
        "historical": [{"month": "2025-12", "revenue": 12_000.0}],
        "forecast": [{"month": "2026-01", "revenue": 12_100.0}],
        "unavailable_reason": None,
    }

    with (
        patch(
            "app.services.forecasting.ets.cache_get_json",
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.forecasting.ets._compute_ets_forecast",
        ) as mock_compute,
        patch(
            "app.services.forecasting.ets.cache_set_json",
        ) as mock_set,
    ):
        result = build_ets_forecast(db=db, client_id=7)

    assert result == cached
    mock_get.assert_called_once()
    mock_compute.assert_not_called()
    mock_set.assert_not_called()
    db.execute.assert_not_called()
