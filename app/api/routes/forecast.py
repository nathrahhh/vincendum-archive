from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.forecasting_engine import build_client_forecast

router = APIRouter(tags=["forecast"])


@router.get("/clients/{client_id}/forecast")
def get_client_forecast(client_id: int, db: Session = Depends(get_db)) -> dict:
    return build_client_forecast(db, client_id)