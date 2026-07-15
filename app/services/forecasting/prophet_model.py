from datetime import date, datetime
from typing import Any

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.models.client_financial import ClientFinancialORM


FORECAST_MONTHS = 6

BEST_CASE_ADJUSTMENT = 0.03
WORST_CASE_ADJUSTMENT = -0.03


def _parse_month(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        return date.fromisoformat(value[:10])

    raise ValueError(f"Unsupported month value: {value!r}")


def _fetch_revenue_history(
    db: Session,
    client_id: int,
) -> list[ClientFinancialORM]:

    return (
        db.query(ClientFinancialORM)
        .filter(
            ClientFinancialORM.client_id == client_id
        )
        .order_by(
            ClientFinancialORM.month.asc()
        )
        .all()
    )


def _build_scenarios(
    revenue: float,
    revenue_growth_rate: float,
) -> dict[str, float]:

    return {
        "base": round(
            revenue * (1 + revenue_growth_rate),
            2,
        ),

        "best": round(
            revenue * (
                1
                + revenue_growth_rate
                + BEST_CASE_ADJUSTMENT
            ),
            2,
        ),

        "worst": round(
            revenue * (
                1
                + revenue_growth_rate
                + WORST_CASE_ADJUSTMENT
            ),
            2,
        ),
    }


def build_client_forecast(
    db: Session,
    client_id: int,
    revenue_growth_rate: float,
) -> dict[str, Any]:

    history = _fetch_revenue_history(
        db=db,
        client_id=client_id,
    )


    if len(history) < 2:
        return {
            "client_id": client_id,
            "forecast": [],
        }


    prophet_df = pd.DataFrame(
        [
            {
                "ds": _parse_month(row.month),
                "y": float(row.revenue),
            }
            for row in history
        ]
    )


    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )


    model.fit(prophet_df)


    future = model.make_future_dataframe(
        periods=FORECAST_MONTHS,
        freq="MS",
    )


    forecast = model.predict(
        future
    )


    future_forecast = forecast.tail(
        FORECAST_MONTHS
    )


    result = []


    for _, row in future_forecast.iterrows():

        prophet_revenue = float(
            row["yhat"]
        )

        scenarios = _build_scenarios(
            revenue=prophet_revenue,
            revenue_growth_rate=revenue_growth_rate,
        )


        result.append(
            {
                "month": row["ds"].strftime("%Y-%m"),

                # Prophet base prediction
                "revenue": round(
                    prophet_revenue,
                    2,
                ),

                # Scenario lines for frontend chart
                "base": scenarios["base"],

                "best": scenarios["best"],

                "worst": scenarios["worst"],


                # Prophet uncertainty interval
                "lower_bound": round(
                    float(row["yhat_lower"]),
                    2,
                ),

                "upper_bound": round(
                    float(row["yhat_upper"]),
                    2,
                ),
            }
        )


    return {
        "client_id": client_id,
        "forecast": result,
    }