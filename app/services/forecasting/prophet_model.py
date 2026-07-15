from datetime import date, datetime
from typing import Any

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.models.client_financial import ClientFinancialORM


FORECAST_MONTHS = 6
HISTORICAL_MONTHS = 6

BEST_CASE_ADJUSTMENT = 0.03
WORST_CASE_ADJUSTMENT = -0.03


def _parse_month(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        return date.fromisoformat(value[:10])

    raise ValueError(
        f"Unsupported month value: {value!r}"
    )


def _format_month(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")

    return str(value)[:7]


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
            revenue
            * (
                1
                + revenue_growth_rate
                + BEST_CASE_ADJUSTMENT
            ),
            2,
        ),

        "worst": round(
            revenue
            * (
                1
                + revenue_growth_rate
                + WORST_CASE_ADJUSTMENT
            ),
            2,
        ),
    }


def _train_prophet(
    dataframe: pd.DataFrame,
) -> Prophet:

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )

    model.fit(dataframe)

    return model


def _build_prophet_dataframe(
    history: list[ClientFinancialORM],
    field: str,
) -> pd.DataFrame:

    return pd.DataFrame(
        [
            {
                "ds": _parse_month(row.month),
                "y": float(getattr(row, field)),
            }
            for row in history
        ]
    )


def build_client_forecast(
    db: Session,
    client_id: int,
    revenue_growth_rate: float,
) -> dict[str, Any]:

    history = _fetch_revenue_history(
        db=db,
        client_id=client_id,
    )


    if len(history) < 12:
        raise ValueError(
            "Prophet requires at least 12 months of data"
        )


    # -----------------------------
    # Historical chart data
    # -----------------------------

    historical = [
        {
            "month": _format_month(row.month),

            "revenue": float(row.revenue),

            "gross_profit": float(row.gross_profit),
        }
        for row in history[-HISTORICAL_MONTHS:]
    ]


    # -----------------------------
    # Revenue Prophet model
    # -----------------------------

    revenue_df = _build_prophet_dataframe(
        history,
        "revenue",
    )

    revenue_model = _train_prophet(
        revenue_df
    )


    # -----------------------------
    # Gross profit Prophet model
    # -----------------------------

    gross_profit_df = _build_prophet_dataframe(
        history,
        "gross_profit",
    )

    gross_profit_model = _train_prophet(
        gross_profit_df
    )


    # -----------------------------
    # Future prediction
    # -----------------------------

    future = revenue_model.make_future_dataframe(
        periods=FORECAST_MONTHS,
        freq="MS",
    )


    revenue_prediction = revenue_model.predict(
        future
    )


    gross_profit_prediction = (
        gross_profit_model.predict(
            future
        )
    )


    revenue_future = (
        revenue_prediction
        .tail(FORECAST_MONTHS)
        .reset_index(drop=True)
    )


    gross_profit_future = (
        gross_profit_prediction
        .tail(FORECAST_MONTHS)
        .reset_index(drop=True)
    )


    result = []


    for index in range(FORECAST_MONTHS):

        revenue_row = revenue_future.iloc[index]

        gross_profit_row = (
            gross_profit_future.iloc[index]
        )


        predicted_revenue = float(
            revenue_row["yhat"]
        )


        scenarios = _build_scenarios(
            revenue=predicted_revenue,
            revenue_growth_rate=revenue_growth_rate,
        )


        result.append(
            {
                "month": revenue_row["ds"].strftime(
                    "%Y-%m"
                ),

                "revenue": round(
                    predicted_revenue,
                    2,
                ),

                "gross_profit": round(
                    float(
                        gross_profit_row["yhat"]
                    ),
                    2,
                ),

                "base": scenarios["base"],

                "best": scenarios["best"],

                "worst": scenarios["worst"],

                "lower_bound": round(
                    float(
                        revenue_row["yhat_lower"]
                    ),
                    2,
                ),

                "upper_bound": round(
                    float(
                        revenue_row["yhat_upper"]
                    ),
                    2,
                ),
            }
        )


    return {
        "client_id": client_id,

        "model_type": "prophet",

        "historical": historical,

        "forecast": result,
    }