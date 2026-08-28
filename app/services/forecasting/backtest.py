"""Holdout backtesting for statistical monthly revenue forecasting models."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.forecasting.shared import (
    FORECAST_MONTHS,
    _add_months,
    _fetch_client_financials,
    _parse_month,
)
from app.services.forecasting.ets import forecast_ets_from_history
from app.services.forecasting.holt_winters import forecast_holt_winters_from_history
from app.services.forecasting.naive import forecast_naive_from_history
from app.services.forecasting.prophet import forecast_prophet_from_history
from app.services.forecasting.seasonal_naive import forecast_seasonal_naive_from_history

# Hold out the same horizon the live forecast endpoints produce.
HOLDOUT_MONTHS = FORECAST_MONTHS

UNAVAILABLE_INSUFFICIENT_HISTORY = "insufficient_history"
UNAVAILABLE_NON_CONSECUTIVE_MONTHS = "non_consecutive_months"
UNAVAILABLE_MODEL_FIT_FAILED = "model_fit_failed"

STATISTICAL_BACKTEST_MODELS: tuple[str, ...] = (
    "naive",
    "seasonal_naive",
    "ets",
    "holt_winters",
    "prophet",
)

ForecastFromHistory = Callable[
    [list[tuple[date, float]]],
    tuple[list[dict[str, Any]], str | None],
]


def _months_are_consecutive(months: list[date]) -> bool:
    for index in range(1, len(months)):
        if _add_months(months[index - 1], 1) != months[index]:
            return False
    return True


def _mean_absolute_error(
    actuals: list[float],
    predictions: list[float],
) -> float:
    errors = [abs(pred - actual) for pred, actual in zip(predictions, actuals)]
    return round(sum(errors) / len(errors), 2)


def _unavailable_model_result(model: str, reason: str) -> dict[str, Any]:
    return {
        "model": model,
        "mae": None,
        "available": False,
        "unavailable_reason": reason,
    }


def _evaluate_model(
    *,
    model: str,
    forecast_fn: ForecastFromHistory,
    train: list[tuple[date, float]],
    holdout: list[tuple[date, float]],
) -> dict[str, Any]:
    try:
        forecast, reason = forecast_fn(train)
    except Exception:
        return _unavailable_model_result(model, UNAVAILABLE_MODEL_FIT_FAILED)

    if reason is not None:
        return _unavailable_model_result(model, reason)

    if len(forecast) != len(holdout):
        return _unavailable_model_result(model, UNAVAILABLE_MODEL_FIT_FAILED)

    # Ensure predictions align to the chronological holdout months.
    for index, (holdout_month, _) in enumerate(holdout):
        if forecast[index]["month"] != holdout_month.strftime("%Y-%m"):
            return _unavailable_model_result(model, UNAVAILABLE_MODEL_FIT_FAILED)

    actuals = [revenue for _, revenue in holdout]
    predictions = [float(point["revenue"]) for point in forecast]
    return {
        "model": model,
        "mae": _mean_absolute_error(actuals, predictions),
        "available": True,
        "unavailable_reason": None,
    }


def build_forecast_backtest(
    db: Session,
    client_id: int,
) -> dict[str, Any]:
    """
    Compare statistical models on a chronological holdout of recent months.

    Does not return a future forecast — only historical MAE comparison.
    """
    financial_history = _fetch_client_financials(db, client_id)

    # Preserve chronological order from SQL (ASC by month). Never shuffle.
    parsed: list[tuple[date, float]] = [
        (_parse_month(row["month"]), float(row["revenue"]))
        for row in financial_history
    ]

    if len(parsed) < HOLDOUT_MONTHS + 1:
        results = [
            _unavailable_model_result(model, UNAVAILABLE_INSUFFICIENT_HISTORY)
            for model in STATISTICAL_BACKTEST_MODELS
        ]
        return {
            "client_id": client_id,
            "metric": "mae",
            "holdout_months": HOLDOUT_MONTHS,
            "best_model": None,
            "results": results,
        }

    months = [month for month, _ in parsed]
    if not _months_are_consecutive(months):
        results = [
            _unavailable_model_result(model, UNAVAILABLE_NON_CONSECUTIVE_MONTHS)
            for model in STATISTICAL_BACKTEST_MODELS
        ]
        return {
            "client_id": client_id,
            "metric": "mae",
            "holdout_months": HOLDOUT_MONTHS,
            "best_model": None,
            "results": results,
        }

    train = parsed[:-HOLDOUT_MONTHS]
    holdout = parsed[-HOLDOUT_MONTHS:]

    model_forecasters: dict[str, ForecastFromHistory] = {
        "naive": lambda history: forecast_naive_from_history(
            history, horizon=HOLDOUT_MONTHS
        ),
        "seasonal_naive": lambda history: forecast_seasonal_naive_from_history(
            history, horizon=HOLDOUT_MONTHS
        ),
        "ets": lambda history: forecast_ets_from_history(
            history, horizon=HOLDOUT_MONTHS
        ),
        "holt_winters": lambda history: forecast_holt_winters_from_history(
            history, horizon=HOLDOUT_MONTHS
        ),
        "prophet": lambda history: forecast_prophet_from_history(
            history, horizon=HOLDOUT_MONTHS
        ),
    }

    results: list[dict[str, Any]] = []
    for model in STATISTICAL_BACKTEST_MODELS:
        results.append(
            _evaluate_model(
                model=model,
                forecast_fn=model_forecasters[model],
                train=train,
                holdout=holdout,
            )
        )

    available = [row for row in results if row["available"]]
    best_model = None
    if available:
        best_model = min(available, key=lambda row: (row["mae"], row["model"]))["model"]

    return {
        "client_id": client_id,
        "metric": "mae",
        "holdout_months": HOLDOUT_MONTHS,
        "best_model": best_model,
        "results": results,
    }
