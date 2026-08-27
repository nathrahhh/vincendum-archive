from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.db import get_db
from app.models.client import ClientORM
from app.models.schemas import (
    DeterministicForecastResponse,
    ForecastBacktestResponse,
    StatisticalForecastResponse,
)
from app.models.user import UserORM
from app.services.forecasting.backtest import build_forecast_backtest
from app.services.forecasting.deterministic import build_deterministic_forecast
from app.services.forecasting.ets import build_ets_forecast
from app.services.forecasting.holt_winters import build_holt_winters_forecast
from app.services.forecasting.naive import build_naive_forecast
from app.services.forecasting.prophet import build_prophet_forecast
from app.services.forecasting.seasonal_naive import build_seasonal_naive_forecast

router = APIRouter(tags=["forecast"])

SUPPORTED_MODELS = {
    "deterministic",
    "prophet",
    "naive",
    "seasonal_naive",
    "ets",
    "holt_winters",
}

ForecastResponse = DeterministicForecastResponse | StatisticalForecastResponse


def _run_forecast(
    *,
    db: Session,
    client_id: int,
    model: str,
    revenue_growth_rate: float,
) -> ForecastResponse:
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

    if selected_model == "naive":
        return build_naive_forecast(db=db, client_id=client_id)

    if selected_model == "seasonal_naive":
        return build_seasonal_naive_forecast(db=db, client_id=client_id)

    if selected_model == "ets":
        return build_ets_forecast(db=db, client_id=client_id)

    if selected_model == "holt_winters":
        return build_holt_winters_forecast(db=db, client_id=client_id)

    return build_deterministic_forecast(
        db=db,
        client_id=client_id,
        revenue_growth_rate=revenue_growth_rate,
    )


@router.get(
    "/clients/{client_id}/forecast",
    response_model=ForecastResponse,
)
def get_client_forecast(
    client_id: int,
    model: str = Query(
        "deterministic",
        description=(
            "Forecasting model to use: deterministic, prophet, naive, "
            "seasonal_naive, ets, or holt_winters"
        ),
    ),
    revenue_growth_rate: float = Query(
        0.05,
        description="Expected monthly revenue growth rate (e.g. 0.05 = 5%). Used by deterministic model only.",
    ),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
) -> ForecastResponse:
    return _run_forecast(
        db=db,
        client_id=client_id,
        model=model,
        revenue_growth_rate=revenue_growth_rate,
    )


@router.get(
    "/client/me/forecast",
    response_model=ForecastResponse,
)
def get_my_client_forecast(
    model: str = Query(
        "deterministic",
        description=(
            "Forecasting model to use: deterministic, prophet, naive, "
            "seasonal_naive, ets, or holt_winters"
        ),
    ),
    revenue_growth_rate: float = Query(
        0.05,
        description="Expected monthly revenue growth rate (e.g. 0.05 = 5%). Used by deterministic model only.",
    ),
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> ForecastResponse:
    return _run_forecast(
        db=db,
        client_id=current_client.id,
        model=model,
        revenue_growth_rate=revenue_growth_rate,
    )


@router.get(
    "/clients/{client_id}/forecast/backtest",
    response_model=ForecastBacktestResponse,
)
def get_client_forecast_backtest(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
) -> ForecastBacktestResponse:
    return build_forecast_backtest(db=db, client_id=client_id)


@router.get(
    "/client/me/forecast/backtest",
    response_model=ForecastBacktestResponse,
)
def get_my_client_forecast_backtest(
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> ForecastBacktestResponse:
    return build_forecast_backtest(db=db, client_id=current_client.id)
