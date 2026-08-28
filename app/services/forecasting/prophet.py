from typing import Any
from datetime import date

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.services.cache.redis_client import DEFAULT_TTL_SECONDS, cache_get_json, cache_set_json
from app.services.forecasting.cache_keys import prophet_forecast_cache_key
from app.services.forecasting.shared import (
    FORECAST_MONTHS,
    _fetch_client_financials,
    _format_month,
    _parse_month,
)

# Prophet needs at least two chronological points to fit a usable series.
MIN_OBSERVATIONS = 2

UNAVAILABLE_INSUFFICIENT_HISTORY = "insufficient_history"
UNAVAILABLE_MODEL_FIT_FAILED = "model_fit_failed"


def forecast_prophet_from_history(
    history: list[tuple[date, float]],
    *,
    horizon: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Forecast from chronological (month, revenue) observations.

    Returns (forecast_points, unavailable_reason).
    Does not change Prophet configuration; only adapts output to revenue-only points.
    """
    if len(history) < MIN_OBSERVATIONS:
        return [], UNAVAILABLE_INSUFFICIENT_HISTORY

    history_df = pd.DataFrame(
        {
            "ds": pd.to_datetime([month for month, _ in history]),
            "y": [revenue for _, revenue in history],
        }
    )

    try:
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        model.fit(history_df)
        future = model.make_future_dataframe(
            periods=horizon,
            freq="MS",
        )
        prediction = model.predict(future)
    except Exception:
        return [], UNAVAILABLE_MODEL_FIT_FAILED

    last_historical_month = history_df["ds"].max()
    future_rows = prediction[prediction["ds"] > last_historical_month]

    forecast = [
        {
            "month": _format_month(row.ds),
            "revenue": round(float(row.yhat), 2),
        }
        for row in future_rows.itertuples(index=False)
    ]

    if len(forecast) != horizon:
        return [], UNAVAILABLE_MODEL_FIT_FAILED

    return forecast, None


def build_prophet_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    cache_key = prophet_forecast_cache_key(client_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    result = _compute_prophet_forecast(db=db, client_id=client_id)

    # Do not cache empty / missing-history responses.
    forecast = result.get("forecast")
    if isinstance(forecast, list) and forecast:
        cache_set_json(cache_key, result, ttl_seconds=DEFAULT_TTL_SECONDS)

    return result


def _compute_prophet_forecast(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    financial_history = _fetch_client_financials(db, client_id)

    if not financial_history:
        return {
            "client_id": client_id,
            "model": "prophet",
            "historical": [],
            "forecast": [],
            "unavailable_reason": None,
        }

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

    forecast, reason = forecast_prophet_from_history(
        parsed,
        horizon=FORECAST_MONTHS,
    )

    return {
        "client_id": client_id,
        "model": "prophet",
        "historical": historical,
        "forecast": forecast,
        "unavailable_reason": reason,
    }
