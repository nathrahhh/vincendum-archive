from typing import Any

from sqlalchemy.orm import Session

from app.services.forecasting.deterministic import (
    build_client_forecast as build_deterministic_forecast,
)


def build_client_forecast(
    db: Session,
    client_id: int,
    revenue_growth_rate: float,
) -> dict[str, Any]:
    return build_deterministic_forecast(
        db=db,
        client_id=client_id,
        revenue_growth_rate=revenue_growth_rate,
    )
