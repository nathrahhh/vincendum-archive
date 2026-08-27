"""Unit tests for the Seasonal Naive forecasting model."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.forecasting.cache_keys import seasonal_naive_forecast_cache_key
from app.services.forecasting.deterministic import _add_months
from app.services.forecasting.seasonal_naive import (
    UNAVAILABLE_INSUFFICIENT_HISTORY,
    UNAVAILABLE_NON_CONSECUTIVE_MONTHS,
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
    # Distinct revenues encode the calendar month so seasonal offsets are obvious.
    return [
        _row(_add_months(start, offset), float((offset + 1) * 1_000))
        for offset in range(months)
    ]


def test_seasonal_naive_cache_key_includes_client_id() -> None:
    assert (
        seasonal_naive_forecast_cache_key(7)
        == "forecast:seasonal_naive:7"
    )


def test_seasonal_naive_forecast_uses_same_month_prior_year() -> None:
    db = MagicMock()
    # 12 consecutive months ending 2026-08.
    history = _consecutive_history(start=date(2025, 9, 1), months=12)
    # revenues: 2025-09=1000 ... 2026-08=12000

    with (
        patch(
            "app.services.forecasting.seasonal_naive.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.seasonal_naive._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.seasonal_naive.cache_set_json",
            return_value=True,
        ) as mock_set,
    ):
        result = build_seasonal_naive_forecast(db=db, client_id=7)

    assert result["client_id"] == 7
    assert result["model"] == "seasonal_naive"
    assert result["unavailable_reason"] is None
    assert len(result["historical"]) == 12
    assert result["historical"][0] == {"month": "2025-09", "revenue": 1_000.0}
    assert result["historical"][-1] == {"month": "2026-08", "revenue": 12_000.0}

    assert [point["month"] for point in result["forecast"]] == [
        "2026-09",
        "2026-10",
        "2026-11",
        "2026-12",
        "2027-01",
        "2027-02",
    ]
    # 2026-09 <- 2025-09 (1000), ..., 2027-02 <- 2026-02 (6000)
    assert [point["revenue"] for point in result["forecast"]] == [
        1_000.0,
        2_000.0,
        3_000.0,
        4_000.0,
        5_000.0,
        6_000.0,
    ]
    mock_set.assert_called_once()


def test_seasonal_naive_insufficient_history_does_not_fabricate_forecast() -> None:
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
        patch(
            "app.services.forecasting.seasonal_naive.cache_set_json",
        ) as mock_set,
    ):
        result = build_seasonal_naive_forecast(db=db, client_id=7)

    assert result["model"] == "seasonal_naive"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_INSUFFICIENT_HISTORY
    assert len(result["historical"]) == 11
    mock_set.assert_not_called()


def test_seasonal_naive_missing_calendar_months_is_unavailable() -> None:
    db = MagicMock()
    # 12 rows but with a gap in the recent window (skip 2026-03).
    history = (
        _consecutive_history(start=date(2025, 9, 1), months=6)
        + _consecutive_history(start=date(2026, 4, 1), months=6)
    )
    assert len(history) == 12

    with (
        patch(
            "app.services.forecasting.seasonal_naive.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.seasonal_naive._fetch_client_financials",
            return_value=history,
        ),
        patch(
            "app.services.forecasting.seasonal_naive.cache_set_json",
        ) as mock_set,
    ):
        result = build_seasonal_naive_forecast(db=db, client_id=7)

    assert result["model"] == "seasonal_naive"
    assert result["forecast"] == []
    assert result["unavailable_reason"] == UNAVAILABLE_NON_CONSECUTIVE_MONTHS
    assert len(result["historical"]) == 12
    mock_set.assert_not_called()


def test_seasonal_naive_cache_hit_skips_recalculation() -> None:
    db = MagicMock()
    cached = {
        "client_id": 7,
        "model": "seasonal_naive",
        "historical": [{"month": "2026-08", "revenue": 12_000.0}],
        "forecast": [{"month": "2026-09", "revenue": 1_000.0}],
        "unavailable_reason": None,
    }

    with (
        patch(
            "app.services.forecasting.seasonal_naive.cache_get_json",
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.forecasting.seasonal_naive._compute_seasonal_naive_forecast",
        ) as mock_compute,
        patch(
            "app.services.forecasting.seasonal_naive.cache_set_json",
        ) as mock_set,
    ):
        result = build_seasonal_naive_forecast(db=db, client_id=7)

    assert result == cached
    mock_get.assert_called_once()
    mock_compute.assert_not_called()
    mock_set.assert_not_called()
    db.execute.assert_not_called()
