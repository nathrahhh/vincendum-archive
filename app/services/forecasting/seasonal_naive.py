"""Seasonal Naive forecast: each future month equals same month 12 months earlier."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.services.cache.redis_client import DEFAULT_TTL_SECONDS, cache_get_json, cache_set_json
from app.services.forecasting.cache_keys import seasonal_naive_forecast_cache_key
from app.services.forecasting.shared import (
    FORECAST_MONTHS,
    _add_months,
    _fetch_client_financials,
    _format_month,
    _parse_month,
)

SEASONAL_PERIOD = 12

UNAVAILABLE_INSUFFICIENT_HISTORY = "insufficient_history"
UNAVAILABLE_NON_CONSECUTIVE_MONTHS = "non_consecutive_months"


def _months_are_consecutive(months: list[date]) -> bool:
    for index in range(1, len(months)):
        if _add_months(months[index - 1], 1) != months[index]:
            return False
    return True


def forecast_seasonal_naive_from_history(
    history: list[tuple[date, float]],
    *,
    horizon: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Forecast from chronological (month, revenue) observations.

    Returns (forecast_points, unavailable_reason).
    """
    if len(history) < SEASONAL_PERIOD:
        return [], UNAVAILABLE_INSUFFICIENT_HISTORY

    recent = history[-SEASONAL_PERIOD:]
    recent_months = [month for month, _ in recent]
    if not _months_are_consecutive(recent_months):
        return [], UNAVAILABLE_NON_CONSECUTIVE_MONTHS

    revenue_by_month = {month: revenue for month, revenue in history}
    latest_month = history[-1][0]

    forecast: list[dict[str, Any]] = []
    for offset in range(1, horizon + 1):
        target_month = _add_months(latest_month, offset)
        seasonal_month = _add_months(target_month, -SEASONAL_PERIOD)
        seasonal_revenue = revenue_by_month.get(seasonal_month)
        if seasonal_revenue is None:
            return [], UNAVAILABLE_INSUFFICIENT_HISTORY
        forecast.append(
            {
                "month": _format_month(target_month),
                "revenue": seasonal_revenue,
            }
        )
    return forecast, None


def build_seasonal_naive_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    cache_key = seasonal_naive_forecast_cache_key(client_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    result = _compute_seasonal_naive_forecast(db=db, client_id=client_id)

    # Do not cache empty / unavailable forecasts.
    forecast = result.get("forecast")
    if isinstance(forecast, list) and forecast:
        cache_set_json(cache_key, result, ttl_seconds=DEFAULT_TTL_SECONDS)

    return result


def _unavailable_result(
    *,
    client_id: int,
    historical: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return {
        "client_id": client_id,
        "model": "seasonal_naive",
        "historical": historical,
        "forecast": [],
        "unavailable_reason": reason,
    }


def _compute_seasonal_naive_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    financial_history = _fetch_client_financials(db, client_id)

    if not financial_history:
        return _unavailable_result(
            client_id=client_id,
            historical=[],
            reason=UNAVAILABLE_INSUFFICIENT_HISTORY,
        )

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

    forecast, reason = forecast_seasonal_naive_from_history(
        parsed,
        horizon=FORECAST_MONTHS,
    )
    if reason is not None:
        return _unavailable_result(
            client_id=client_id,
            historical=historical,
            reason=reason,
        )

    return {
        "client_id": client_id,
        "model": "seasonal_naive",
        "historical": historical,
        "forecast": forecast,
        "unavailable_reason": None,
    }
