from unittest.mock import patch

from app.services.forecasting.cache_keys import (
    ets_forecast_cache_key,
    holt_winters_forecast_cache_key,
    invalidate_forecast_cache,
    naive_forecast_cache_key,
    prophet_forecast_cache_key,
    seasonal_naive_forecast_cache_key,
)


def test_statistical_forecast_cache_keys():
    assert prophet_forecast_cache_key(7) == "forecast:prophet:7"
    assert naive_forecast_cache_key(7) == "forecast:naive:7"
    assert seasonal_naive_forecast_cache_key(7) == "forecast:seasonal_naive:7"
    assert ets_forecast_cache_key(7) == "forecast:ets:7"
    assert holt_winters_forecast_cache_key(7) == "forecast:holt_winters:7"


def test_invalidate_forecast_cache_deletes_statistical_keys():
    with patch(
        "app.services.forecasting.cache_keys.cache_delete",
    ) as mock_delete:
        invalidate_forecast_cache(42)

    assert mock_delete.call_args_list[0].args == ("forecast:naive:42",)
    assert mock_delete.call_args_list[1].args == ("forecast:seasonal_naive:42",)
    assert mock_delete.call_args_list[2].args == ("forecast:ets:42",)
    assert mock_delete.call_args_list[3].args == ("forecast:holt_winters:42",)
    assert mock_delete.call_args_list[4].args == ("forecast:prophet:42",)
