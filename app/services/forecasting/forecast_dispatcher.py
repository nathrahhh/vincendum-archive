from typing import Any

from sqlalchemy.orm import Session

from app.models.client_financial import ClientFinancialORM

from app.services.forecasting.deterministic import (
    build_client_forecast as build_deterministic_forecast,
)

from app.services.forecasting.prophet_model import (
    build_client_forecast as build_prophet_forecast,
)


MINIMUM_PROPHET_HISTORY = 12


def _has_enough_history(
    db: Session,
    client_id: int,
) -> bool:

    count = (
        db.query(ClientFinancialORM)
        .filter(
            ClientFinancialORM.client_id == client_id
        )
        .count()
    )

    return count >= MINIMUM_PROPHET_HISTORY



def build_client_forecast(
    db: Session,
    client_id: int,
    revenue_growth_rate: float,
) -> dict[str, Any]:


    if _has_enough_history(
        db=db,
        client_id=client_id,
    ):

        forecast = build_prophet_forecast(
            db=db,
            client_id=client_id,
            revenue_growth_rate=revenue_growth_rate,
        )

        forecast["model_type"] = "prophet"

        return forecast



    forecast = build_deterministic_forecast(
        db=db,
        client_id=client_id,
        revenue_growth_rate=revenue_growth_rate,
    )

    forecast["model_type"] = "deterministic"

    return forecast