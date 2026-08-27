"""Unit tests for the Naive forecasting model."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.forecasting.cache_keys import naive_forecast_cache_key
from app.services.forecasting.naive import build_naive_forecast


def _history_rows() -> list[dict]:
    return [
        {
            "month": date(2026, 1, 1),
            "revenue": 100_000.0,
            "cogs": 0.0,
            "opex": 0.0,
            "gross_profit": 100_000.0,
            "cash_balance": 0.0,
        },
        {
            "month": date(2026, 2, 1),
            "revenue": 110_000.0,
            "cogs": 0.0,
            "opex": 0.0,
            "gross_profit": 110_000.0,
            "cash_balance": 0.0,
        },
        {
            "month": date(2026, 3, 1),
            "revenue": 120_000.0,
            "cogs": 0.0,
            "opex": 0.0,
            "gross_profit": 120_000.0,
            "cash_balance": 0.0,
        },
    ]


def test_naive_forecast_cache_key_includes_client_id() -> None:
    assert naive_forecast_cache_key(7) == "forecast:naive:7"


def test_naive_produces_six_month_forecast_from_latest_revenue() -> None:
    db = MagicMock()

    with (
        patch(
            "app.services.forecasting.naive.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.naive._fetch_client_financials",
            return_value=_history_rows(),
        ),
        patch(
            "app.services.forecasting.naive.cache_set_json",
            return_value=True,
        ) as mock_set,
    ):
        result = build_naive_forecast(db=db, client_id=7)

    assert result["client_id"] == 7
    assert result["model"] == "naive"
    assert result["historical"] == [
        {"month": "2026-01", "revenue": 100_000.0},
        {"month": "2026-02", "revenue": 110_000.0},
        {"month": "2026-03", "revenue": 120_000.0},
    ]
    assert len(result["forecast"]) == 6
    assert [point["month"] for point in result["forecast"]] == [
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
    ]
    assert all(point["revenue"] == 120_000.0 for point in result["forecast"])
    mock_set.assert_called_once()


def test_naive_missing_history_returns_empty_forecast_and_does_not_cache() -> None:
    db = MagicMock()

    with (
        patch(
            "app.services.forecasting.naive.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.naive._fetch_client_financials",
            return_value=[],
        ),
        patch(
            "app.services.forecasting.naive.cache_set_json",
        ) as mock_set,
    ):
        result = build_naive_forecast(db=db, client_id=7)

    assert result == {
        "client_id": 7,
        "model": "naive",
        "historical": [],
        "forecast": [],
        "unavailable_reason": None,
    }
    mock_set.assert_not_called()


def test_naive_cache_hit_skips_recalculation() -> None:
    db = MagicMock()
    cached = {
        "client_id": 7,
        "model": "naive",
        "historical": [{"month": "2026-03", "revenue": 120_000.0}],
        "forecast": [{"month": "2026-04", "revenue": 120_000.0}],
    }

    with (
        patch(
            "app.services.forecasting.naive.cache_get_json",
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.forecasting.naive._compute_naive_forecast",
        ) as mock_compute,
        patch(
            "app.services.forecasting.naive.cache_set_json",
        ) as mock_set,
    ):
        result = build_naive_forecast(db=db, client_id=7)

    assert result == cached
    mock_get.assert_called_once()
    mock_compute.assert_not_called()
    mock_set.assert_not_called()
    db.execute.assert_not_called()
