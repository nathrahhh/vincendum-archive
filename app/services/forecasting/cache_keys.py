"""Forecasting cache key helpers and invalidation."""

from __future__ import annotations

from app.services.cache.redis_client import cache_delete


def prophet_forecast_cache_key(client_id: int) -> str:
    return f"forecast:prophet:{client_id}"


def naive_forecast_cache_key(client_id: int) -> str:
    return f"forecast:naive:{client_id}"


def seasonal_naive_forecast_cache_key(client_id: int) -> str:
    return f"forecast:seasonal_naive:{client_id}"


def ets_forecast_cache_key(client_id: int) -> str:
    return f"forecast:ets:{client_id}"


def holt_winters_forecast_cache_key(client_id: int) -> str:
    return f"forecast:holt_winters:{client_id}"


def invalidate_forecast_cache(client_id: int) -> None:
    """
    Remove cached forecasts for a client (naive, seasonal naive, ETS,
    Holt-Winters, Prophet).

    Safe to call when Redis is unavailable; failures are swallowed by helpers.
    """
    cache_delete(naive_forecast_cache_key(client_id))
    cache_delete(seasonal_naive_forecast_cache_key(client_id))
    cache_delete(ets_forecast_cache_key(client_id))
    cache_delete(holt_winters_forecast_cache_key(client_id))
    cache_delete(prophet_forecast_cache_key(client_id))
