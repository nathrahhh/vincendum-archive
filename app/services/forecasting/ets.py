"""ETS (Error-Trend-Seasonal) monthly revenue forecast via statsmodels ETSModel."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

from app.services.cache.redis_client import DEFAULT_TTL_SECONDS, cache_get_json, cache_set_json
from app.services.forecasting.cache_keys import ets_forecast_cache_key
from app.services.forecasting.deterministic import (
    FORECAST_MONTHS,
    _add_months,
    _fetch_client_financials,
    _format_month,
    _parse_month,
)

# Seasonal period for monthly revenue. Seasonal ETS needs two full cycles.
SEASONAL_PERIOD = 12
MIN_SEASONAL_OBSERVATIONS = 2 * SEASONAL_PERIOD
# Non-seasonal additive trend needs a short consecutive series.
# Documented project floor: enough points for a stable level+trend fit.
MIN_OBSERVATIONS = 3

UNAVAILABLE_INSUFFICIENT_HISTORY = "insufficient_history"
UNAVAILABLE_NON_CONSECUTIVE_MONTHS = "non_consecutive_months"
UNAVAILABLE_MODEL_FIT_FAILED = "model_fit_failed"


def _months_are_consecutive(months: list[date]) -> bool:
    for index in range(1, len(months)):
        if _add_months(months[index - 1], 1) != months[index]:
            return False
    return True


def forecast_ets_from_history(
    history: list[tuple[date, float]],
    *,
    horizon: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Forecast from chronological (month, revenue) observations.

    Returns (forecast_points, unavailable_reason).
    """
    if len(history) < MIN_OBSERVATIONS:
        return [], UNAVAILABLE_INSUFFICIENT_HISTORY

    months = [month for month, _ in history]
    if not _months_are_consecutive(months):
        return [], UNAVAILABLE_NON_CONSECUTIVE_MONTHS

    series = pd.Series(
        [revenue for _, revenue in history],
        index=pd.DatetimeIndex(months, freq="MS"),
        dtype=float,
    )

    use_seasonal = len(history) >= MIN_SEASONAL_OBSERVATIONS
    try:
        model = ETSModel(
            series,
            error="add",
            trend="add",
            seasonal="add" if use_seasonal else None,
            seasonal_periods=SEASONAL_PERIOD if use_seasonal else None,
        )
        fitted = model.fit(disp=False)
        predicted = fitted.forecast(horizon)
    except Exception:
        return [], UNAVAILABLE_MODEL_FIT_FAILED

    latest_month = months[-1]
    forecast = [
        {
            "month": _format_month(_add_months(latest_month, offset)),
            "revenue": round(float(predicted.iloc[offset - 1]), 2),
        }
        for offset in range(1, horizon + 1)
    ]
    return forecast, None


def build_ets_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    cache_key = ets_forecast_cache_key(client_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    result = _compute_ets_forecast(db=db, client_id=client_id)

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
        "model": "ets",
        "historical": historical,
        "forecast": [],
        "unavailable_reason": reason,
    }


def _compute_ets_forecast(
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

    forecast, reason = forecast_ets_from_history(
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
        "model": "ets",
        "historical": historical,
        "forecast": forecast,
        "unavailable_reason": None,
    }
