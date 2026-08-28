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


def _fetch_client_financials(
    db: Session,
    client_id: int,
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                month,
                revenue,
                cogs,
                opex,
                gross_profit,
                cash_balance

            FROM client_financials

            WHERE client_id = :client_id

            ORDER BY month ASC
            """
        ),
        {
            "client_id": client_id,
        },
    ).mappings()

    return [dict(row) for row in rows.all()]
