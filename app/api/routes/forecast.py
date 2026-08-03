from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.db import get_db
from app.models.schemas import (
    DeterministicForecastResponse,
    ProphetForecastResponse,
)
from app.models.user import UserORM
from app.services.forecasting.deterministic import build_deterministic_forecast
from app.services.forecasting.prophet import build_prophet_forecast

router = APIRouter(tags=["forecast"])

SUPPORTED_MODELS = {"deterministic", "prophet"}


@router.get(
    "/clients/{client_id}/forecast",
    response_model=DeterministicForecastResponse | ProphetForecastResponse,
)
def get_client_forecast(
    client_id: int,
    model: str = Query(
        "deterministic",
        description="Forecasting model to use: deterministic or prophet",
    ),
    revenue_growth_rate: float = Query(
        0.05,
        description="Expected monthly revenue growth rate (e.g. 0.05 = 5%). Used by deterministic model only.",
    ),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
) -> DeterministicForecastResponse | ProphetForecastResponse:
    selected_model = model.strip().lower()

    if selected_model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid model '{model}'. "
                f"Supported models: {', '.join(sorted(SUPPORTED_MODELS))}."
            ),
        )

    if selected_model == "prophet":
        return build_prophet_forecast(db=db, client_id=client_id)

    return build_deterministic_forecast(
        db=db,
        client_id=client_id,
        revenue_growth_rate=revenue_growth_rate,
    )
