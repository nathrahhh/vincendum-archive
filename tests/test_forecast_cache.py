from unittest.mock import MagicMock, patch

from app.services.forecasting.cache_keys import (
    deterministic_forecast_cache_key,
    invalidate_forecast_cache,
    prophet_forecast_cache_key,
)
from app.services.forecasting.deterministic import build_deterministic_forecast


MOCK_DETERMINISTIC_RESULT = {
    "client_id": 7,
    "assumptions": {"revenue_growth_rate": 0.05},
    "historical": [{"month": "2024-01", "revenue": 100.0}],
    "forecast": [{"month": "2024-02", "revenue": 105.0}],
    "alerts": {"gross_profit_alerts": []},
}


def test_deterministic_cache_key_includes_client_and_rate():
    assert (
        deterministic_forecast_cache_key(7, 0.05)
        == "forecast:deterministic:7:0.05"
    )
    assert prophet_forecast_cache_key(7) == "forecast:prophet:7"


def test_deterministic_cached_result_skips_recalculation():
    db = MagicMock()

    with (
        patch(
            "app.services.forecasting.deterministic.cache_get_json",
            return_value=MOCK_DETERMINISTIC_RESULT,
        ) as mock_get,
        patch(
            "app.services.forecasting.deterministic._compute_deterministic_forecast",
        ) as mock_compute,
        patch(
            "app.services.forecasting.deterministic.cache_set_json",
        ) as mock_set,
    ):
        result = build_deterministic_forecast(
            db=db,
            client_id=7,
            revenue_growth_rate=0.05,
        )

    assert result == MOCK_DETERMINISTIC_RESULT
    mock_get.assert_called_once()
    mock_compute.assert_not_called()
    mock_set.assert_not_called()
    db.execute.assert_not_called()


def test_deterministic_redis_miss_computes_and_caches():
    db = MagicMock()

    with (
        patch(
            "app.services.forecasting.deterministic.cache_get_json",
            return_value=None,
        ),
        patch(
            "app.services.forecasting.deterministic._compute_deterministic_forecast",
            return_value=MOCK_DETERMINISTIC_RESULT,
        ) as mock_compute,
        patch(
            "app.services.forecasting.deterministic.cache_set_json",
            return_value=False,
        ) as mock_set,
    ):
        result = build_deterministic_forecast(
            db=db,
            client_id=7,
            revenue_growth_rate=0.05,
        )

    assert result == MOCK_DETERMINISTIC_RESULT
    mock_compute.assert_called_once()
    mock_set.assert_called_once()


def test_invalidate_forecast_cache_deletes_prophet_and_deterministic_keys():
    with (
        patch(
            "app.services.forecasting.cache_keys.cache_delete",
        ) as mock_delete,
        patch(
            "app.services.forecasting.cache_keys.cache_delete_pattern",
        ) as mock_delete_pattern,
    ):
        invalidate_forecast_cache(42)

    mock_delete.assert_called_once_with("forecast:prophet:42")
    mock_delete_pattern.assert_called_once_with("forecast:deterministic:42:*")
