from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import ClientForecast
from app.services.forecasting.forecast_dispatcher import build_client_forecast

router = APIRouter(tags=["forecast"])


@router.get(
    "/clients/{client_id}/forecast",
    response_model=ClientForecast,
)
def get_client_forecast(
    client_id: int,
    revenue_growth_rate: float = Query(
        0.05,
        description="Expected monthly revenue growth rate (e.g. 0.05 = 5%)",
    ),
    db: Session = Depends(get_db),
) -> ClientForecast:
    return build_client_forecast(
        db=db,
        client_id=client_id,
        revenue_growth_rate=revenue_growth_rate,
    )