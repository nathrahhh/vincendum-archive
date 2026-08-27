"""Forecasting cache key helpers and invalidation."""

from __future__ import annotations

from app.services.cache.redis_client import cache_delete, cache_delete_pattern


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


def deterministic_forecast_cache_key(
    client_id: int,
    revenue_growth_rate: float,
) -> str:
    # Normalize growth rate so equivalent floats share a key.
    rate = f"{float(revenue_growth_rate):.8f}".rstrip("0").rstrip(".")
    return f"forecast:deterministic:{client_id}:{rate}"


def invalidate_forecast_cache(client_id: int) -> None:
    """
    Remove cached forecasts for a client (naive, seasonal naive, ETS,
    Holt-Winters, Prophet, deterministic rates).

    Safe to call when Redis is unavailable; failures are swallowed by helpers.
    """
    cache_delete(naive_forecast_cache_key(client_id))
    cache_delete(seasonal_naive_forecast_cache_key(client_id))
    cache_delete(ets_forecast_cache_key(client_id))
    cache_delete(holt_winters_forecast_cache_key(client_id))
    cache_delete(prophet_forecast_cache_key(client_id))
    cache_delete_pattern(f"forecast:deterministic:{client_id}:*")
