"""Naive statistical forecast: every future month equals latest revenue."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.services.cache.redis_client import DEFAULT_TTL_SECONDS, cache_get_json, cache_set_json
from app.services.forecasting.cache_keys import naive_forecast_cache_key
from app.services.forecasting.deterministic import (
    FORECAST_MONTHS,
    _add_months,
    _fetch_client_financials,
    _format_month,
    _parse_month,
)

UNAVAILABLE_INSUFFICIENT_HISTORY = "insufficient_history"


def forecast_naive_from_history(
    history: list[tuple[date, float]],
    *,
    horizon: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Forecast from chronological (month, revenue) observations.

    Returns (forecast_points, unavailable_reason).
    """
    if not history:
        return [], UNAVAILABLE_INSUFFICIENT_HISTORY

    latest_month, latest_revenue = history[-1]
    forecast = [
        {
            "month": _format_month(_add_months(latest_month, offset)),
            "revenue": latest_revenue,
        }
        for offset in range(1, horizon + 1)
    ]
    return forecast, None


def build_naive_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    cache_key = naive_forecast_cache_key(client_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    result = _compute_naive_forecast(db=db, client_id=client_id)

    # Do not cache empty / missing-history responses.
    forecast = result.get("forecast")
    if isinstance(forecast, list) and forecast:
        cache_set_json(cache_key, result, ttl_seconds=DEFAULT_TTL_SECONDS)

    return result


def _compute_naive_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    financial_history = _fetch_client_financials(db, client_id)

    if not financial_history:
        return {
            "client_id": client_id,
            "model": "naive",
            "historical": [],
            "forecast": [],
            "unavailable_reason": None,
        }

    # History is ordered ASC by month from _fetch_client_financials.
    parsed: list[tuple[date, float]] = [
        (_parse_month(row["month"]), float(row["revenue"]))
        for row in financial_history
    ]
    historical = [
        {
            "month": _format_month(month),
            "revenue": revenue,
        }
        for month, revenue in parsed
    ]

    forecast, reason = forecast_naive_from_history(
        parsed,
        horizon=FORECAST_MONTHS,
    )

    return {
        "client_id": client_id,
        "model": "naive",
        "historical": historical,
        "forecast": forecast,
        "unavailable_reason": reason,
    }
