from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


FORECAST_MONTHS = 6
GROSS_PROFIT_WARNING_THRESHOLD = 0.05  # 5% difference


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
    client_id: int
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
            "client_id": client_id
        }

    ).mappings()

    return [dict(row) for row in rows.all()]


def build_client_forecast(
    db: Session,
    client_id: int,
    revenue_growth_rate: float
) -> dict[str, Any]:

    financial_history = _fetch_client_financials(
        db,
        client_id
    )


    if not financial_history:
        return {
            "client_id": client_id,
            "historical": {},
            "forecast": {}
        }


    # -----------------------------
    # Historical calculations
    # -----------------------------

    historical = []

    cogs_ratios = []
    opex_ratios = []
    gross_profit_margins = []

    gross_profit_alerts = []


    for row in financial_history:

        revenue = float(row["revenue"])
        cogs = float(row["cogs"])
        opex = float(row["opex"])

        reported_gp = (
            float(row["gross_profit"])
            if row["gross_profit"] is not None
            else None
        )


        calculated_gp = revenue - cogs


        # Check client reported GP against calculation

        if reported_gp is not None and revenue != 0:

            difference = abs(
                reported_gp - calculated_gp
            ) / revenue


            if difference > GROSS_PROFIT_WARNING_THRESHOLD:

                gross_profit_alerts.append(
                    {
                        "month": _format_month(row["month"]),
                        "message":
                        "Reported gross profit differs from revenue minus COGS",
                        "difference_pct":
                        round(difference * 100, 2)
                    }
                )


            gross_profit_margins.append(
                reported_gp / revenue
            )


        if revenue != 0:

            cogs_ratios.append(
                cogs / revenue
            )

            opex_ratios.append(
                opex / revenue
            )


        historical.append(
            {
                "month": _format_month(row["month"]),
                "revenue": revenue,
                "cogs": cogs,
                "opex": opex,
                "reported_gross_profit": reported_gp,
                "calculated_gross_profit": calculated_gp,
                "cash_balance": float(row["cash_balance"])
            }
        )


    # -----------------------------
    # Historical averages
    # -----------------------------

    avg_cogs_ratio = (
        sum(cogs_ratios)
        /
        len(cogs_ratios)
    )

    avg_opex_ratio = (
        sum(opex_ratios)
        /
        len(opex_ratios)
    )


    avg_gross_margin = (
        sum(gross_profit_margins)
        /
        len(gross_profit_margins)
        if gross_profit_margins
        else None
    )


    # -----------------------------
    # Forecast
    # -----------------------------


    last_month = financial_history[-1]["month"]

    revenue = float(
        financial_history[-1]["revenue"]
    )

    cash_balance = float(
        financial_history[-1]["cash_balance"]
    )


    forecast = []


    for month_number in range(
        1,
        FORECAST_MONTHS + 1
    ):

        revenue = revenue * (
            1 + revenue_growth_rate
        )


        cogs = revenue * avg_cogs_ratio

        opex = revenue * avg_opex_ratio


        # Method 1:
        # Using historical reported GP margin

        if avg_gross_margin:

            gross_profit_margin_method = (
                revenue * avg_gross_margin
            )

        else:
            gross_profit_margin_method = None


        # Method 2:
        # Revenue - forecast COGS

        gross_profit_cogs_method = (
            revenue - cogs
        )


        gross_profit_difference = None


        if gross_profit_margin_method:

            gross_profit_difference = abs(
                gross_profit_margin_method
                -
                gross_profit_cogs_method
            )


        net_cash_flow = (
            revenue
            -
            cogs
            -
            opex
        )


        cash_balance += net_cash_flow


        forecast.append(
            {
                "month": _format_month(
                    _add_months(
                        last_month,
                        month_number
                    )
                ),

                "revenue": round(revenue, 2),

                "cogs": round(cogs, 2),

                "opex": round(opex, 2),

                "gross_profit_margin_method":
                    round(
                        gross_profit_margin_method,
                        2
                    )
                    if gross_profit_margin_method
                    else None,

                "gross_profit_cogs_method":
                    round(
                        gross_profit_cogs_method,
                        2
                    ),

                "gross_profit_difference":
                    round(
                        gross_profit_difference,
                        2
                    )
                    if gross_profit_difference
                    else None,

                "net_cash_flow":
                    round(net_cash_flow, 2),

                "cash_balance":
                    round(cash_balance, 2)
            }
        )


    return {

        "client_id": client_id,


        "assumptions": {

            "revenue_growth_rate":
                revenue_growth_rate,

            "average_cogs_ratio":
                round(avg_cogs_ratio, 4),

            "average_opex_ratio":
                round(avg_opex_ratio, 4),

            "average_gross_margin":
                round(avg_gross_margin, 4)
                if avg_gross_margin
                else None
        },


        "historical": historical,


        "forecast": forecast,


        "alerts": {

            "gross_profit_alerts":
                gross_profit_alerts

        }

    }