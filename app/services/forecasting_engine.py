from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

FORECAST_MONTHS = 6


def _parse_month(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise ValueError(f"Unsupported month value: {value!r}")


def _format_month(value: Any) -> str:
    return _parse_month(value).strftime("%Y-%m")


def _add_months(month_value: Any, offset: int) -> date:
    current = _parse_month(month_value)
    month_index = current.month - 1 + offset
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _fetch_client_financials(db: Session, client_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT month, revenue, cogs, opex, cash_balance "
            "FROM client_financials "
            "WHERE client_id = :client_id "
            "ORDER BY month ASC"
        ),
        {"client_id": client_id},
    ).mappings()
    return [dict(row) for row in rows.all()]


def build_client_forecast(db: Session, client_id: int) -> dict[str, Any]:
    financial_history = _fetch_client_financials(db, client_id)

    if not financial_history:
        return {
            "client_id": client_id,
            "historical": {"labels": [], "cash_balance": [], "net_cash_flow": []},
            "forecast": {"labels": [], "cash_balance": []},
        }

    historical_labels: list[str] = []
    historical_cash_balance: list[float] = []
    historical_net_cash_flow: list[float] = []

    for row in financial_history:
        revenue = float(row["revenue"])
        cogs = float(row["cogs"])
        opex = float(row["opex"])
        net_cash_flow = revenue - cogs - opex

        historical_labels.append(_format_month(row["month"]))
        historical_cash_balance.append(float(row["cash_balance"]))
        historical_net_cash_flow.append(round(net_cash_flow, 2))

    average_net_cash_flow = sum(historical_net_cash_flow) / len(historical_net_cash_flow)
    last_month = financial_history[-1]["month"]
    previous_cash_balance = historical_cash_balance[-1]

    forecast_labels: list[str] = []
    forecast_cash_balance: list[float] = []

    for period in range(1, FORECAST_MONTHS + 1):
        previous_cash_balance = round(previous_cash_balance + average_net_cash_flow, 2)
        forecast_labels.append(_format_month(_add_months(last_month, period)))
        forecast_cash_balance.append(previous_cash_balance)

    return {
        "client_id": client_id,
        "historical": {
            "labels": historical_labels,
            "cash_balance": historical_cash_balance,
            "net_cash_flow": historical_net_cash_flow,
        },
        "forecast": {
            "labels": forecast_labels,
            "cash_balance": forecast_cash_balance,
        },
    }
