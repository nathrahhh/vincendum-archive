from typing import Any

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.services.forecasting.deterministic import (
    FORECAST_MONTHS,
    _fetch_client_financials,
    _format_month,
    _parse_month,
)


def build_prophet_forecast(
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
        }

    history_df = pd.DataFrame(
        {
            "ds": pd.to_datetime(
                [_parse_month(row["month"]) for row in financial_history]
            ),
            "y": [
                float(row["revenue"])
                for row in financial_history
            ],
        }
    )

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )

    model.fit(history_df)

    future = model.make_future_dataframe(
        periods=FORECAST_MONTHS,
        freq="MS",
    )

    prediction = model.predict(future)

    last_historical_month = history_df["ds"].max()

    future_rows = prediction[
        prediction["ds"] > last_historical_month
    ]

    historical = [
        {
            "month": _format_month(row["month"]),
            "revenue": float(row["revenue"]),
        }
        for row in financial_history
    ]

    forecast = [
        {
            "month": _format_month(row.ds),
            "revenue": round(float(row.yhat), 2),
            "lower_bound": round(float(row.yhat_lower), 2),
            "upper_bound": round(float(row.yhat_upper), 2),
        }
        for row in future_rows.itertuples(index=False)
    ]

    return {
        "client_id": client_id,
        "model": "prophet",
        "historical": historical,
        "forecast": forecast,
    }