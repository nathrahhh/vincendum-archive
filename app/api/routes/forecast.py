from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.forecasting_engine import build_client_forecast

router = APIRouter(tags=["forecast"])


def _month_label(value: object) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m")  # type: ignore[union-attr]
    return str(value)[:7]


@router.get("/clients/{client_id}/financials")
def get_client_financials(client_id: int, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        text(
            "SELECT month, revenue, cogs, opex, cash_balance "
            "FROM client_financials "
            "WHERE client_id = :client_id "
            "ORDER BY month ASC"
        ),
        {"client_id": client_id},
    ).mappings()

    labels: list[str] = []
    revenue: list[float] = []
    cogs: list[float] = []
    opex: list[float] = []
    cash_balance: list[float] = []

    for row in rows:
        labels.append(_month_label(row["month"]))
        revenue.append(float(row["revenue"]))
        cogs.append(float(row["cogs"]))
        opex.append(float(row["opex"]))
        cash_balance.append(float(row["cash_balance"]))

    return {
        "client_id": client_id,
        "labels": labels,
        "revenue": revenue,
        "cogs": cogs,
        "opex": opex,
        "cash_balance": cash_balance,
    }


@router.get("/clients/{client_id}/forecast")
def get_client_forecast(client_id: int, db: Session = Depends(get_db)) -> dict:
    return build_client_forecast(db, client_id)
