#!/usr/bin/env python3
"""Seed consecutive monthly client financials for forecast/backtest manual testing."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from sqlalchemy import func, select

# Allow running as: python scripts/seed_forecast_test_data.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import SessionLocal
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.lender import LenderORM

# Pertama is the existing tenant; slug is the canonical unique identifier used
# across lender-scoped API routes (see app/api/routes/lenders.py).
TARGET_LENDER_SLUG = "pertama"
TARGET_LENDER_NAME = "Pertama"

CLIENT_NAME = "Forecast Test Client"
CLIENT_INDUSTRY = "technology"
CLIENT_CREDIT_LIMIT = 500_000.0
FINANCIAL_STATUS = "APPROVED"

# 30 consecutive months: 2024-01 through 2026-06.
MONTHLY_REVENUE: dict[str, float] = {
    "2024-01": 100_000,
    "2024-02": 102_000,
    "2024-03": 105_000,
    "2024-04": 107_000,
    "2024-05": 110_000,
    "2024-06": 112_000,
    "2024-07": 115_000,
    "2024-08": 117_000,
    "2024-09": 120_000,
    "2024-10": 122_000,
    "2024-11": 125_000,
    "2024-12": 130_000,
    "2025-01": 128_000,
    "2025-02": 131_000,
    "2025-03": 135_000,
    "2025-04": 138_000,
    "2025-05": 142_000,
    "2025-06": 145_000,
    "2025-07": 148_000,
    "2025-08": 152_000,
    "2025-09": 155_000,
    "2025-10": 158_000,
    "2025-11": 162_000,
    "2025-12": 168_000,
    "2026-01": 165_000,
    "2026-02": 169_000,
    "2026-03": 174_000,
    "2026-04": 178_000,
    "2026-05": 183_000,
    "2026-06": 188_000,
}


def _month_date(month_key: str) -> date:
    year, month = month_key.split("-")
    return date(int(year), int(month), 1)


def _financial_fields(revenue: float, month_index: int) -> dict[str, float]:
    """Derive required financial columns from revenue using stable test ratios."""
    cogs = round(revenue * 0.40, 2)
    gross_profit = round(revenue - cogs, 2)
    opex = round(revenue * 0.25, 2)
    cash_balance = round(50_000 + (month_index * 2_500), 2)
    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "opex": opex,
        "cash_balance": cash_balance,
    }


def _get_existing_lender(session) -> LenderORM:
    """
    Resolve the Pertama tenant lender.

    Slug is preferred because it is unique and used for tenant-scoped lookups
    in the application. Name is a secondary fallback for local databases where
    the display name may differ in casing.
    """
    lender = session.execute(
        select(LenderORM).where(LenderORM.slug == TARGET_LENDER_SLUG)
    ).scalar_one_or_none()
    if lender is not None:
        return lender

    lender = session.execute(
        select(LenderORM).where(
            func.lower(LenderORM.name) == TARGET_LENDER_NAME.lower()
        )
    ).scalar_one_or_none()
    if lender is not None:
        return lender

    raise SystemExit(
        f"ERROR: Could not find lender '{TARGET_LENDER_NAME}' "
        f"(slug '{TARGET_LENDER_SLUG}'). "
        "Create the Pertama lender in your local database before running this script."
    )


def _get_or_create_client(session, lender_id: int) -> tuple[ClientORM, bool]:
    client = session.execute(
        select(ClientORM).where(
            ClientORM.name == CLIENT_NAME,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if client is not None:
        return client, False

    client = ClientORM(
        name=CLIENT_NAME,
        industry=CLIENT_INDUSTRY,
        credit_limit=CLIENT_CREDIT_LIMIT,
        lender_id=lender_id,
    )
    session.add(client)
    session.flush()
    return client, True


def _existing_months(session, client_id: int) -> set[date]:
    rows = session.execute(
        select(ClientFinancialORM.month).where(
            ClientFinancialORM.client_id == client_id
        )
    ).scalars()
    return set(rows.all())


def seed_forecast_test_data() -> int:
    created_client = False
    created_months: list[str] = []
    skipped_months: list[str] = []

    with SessionLocal() as session:
        lender = _get_existing_lender(session)
        client, created_client = _get_or_create_client(session, lender.id)
        existing = _existing_months(session, client.id)

        for index, (month_key, revenue) in enumerate(MONTHLY_REVENUE.items()):
            month = _month_date(month_key)
            if month in existing:
                skipped_months.append(month_key)
                continue

            fields = _financial_fields(revenue, index)
            session.add(
                ClientFinancialORM(
                    client_id=client.id,
                    month=month,
                    status=FINANCIAL_STATUS,
                    **fields,
                )
            )
            created_months.append(month_key)

        session.commit()
        client_id = client.id
        lender_name = lender.name
        lender_slug = lender.slug
        lender_id = lender.id

    print("Forecast test data seed complete.")
    print(f"  Lender:      {lender_name} (slug={lender_slug}, id={lender_id})")
    print(f"  Client name: {CLIENT_NAME} ({'created' if created_client else 'existing'})")
    print(f"  Client ID:   {client_id}")
    print(f"  Created:     {len(created_months)} month(s)")
    if created_months:
        print(f"    {created_months[0]} .. {created_months[-1]}")
        print(f"    months: {', '.join(created_months)}")
    else:
        print("    (none - all target months already existed)")

    print(f"  Skipped:     {len(skipped_months)} existing month(s)")
    if skipped_months:
        print(f"    months: {', '.join(skipped_months)}")

    print()
    print("Test with:")
    print(f"  GET /clients/{client_id}/forecast?model=naive")
    print(f"  GET /clients/{client_id}/forecast/backtest")
    print(f"  GET /client/me/forecast/backtest  (when authenticated as this client)")

    return client_id


def verify_seed(client_id: int) -> None:
    with SessionLocal() as session:
        client = session.execute(
            select(ClientORM).where(ClientORM.id == client_id)
        ).scalar_one_or_none()
        lender = None
        if client is not None and client.lender_id is not None:
            lender = session.execute(
                select(LenderORM).where(LenderORM.id == client.lender_id)
            ).scalar_one_or_none()

        rows = session.execute(
            select(ClientFinancialORM)
            .where(ClientFinancialORM.client_id == client_id)
            .order_by(ClientFinancialORM.month.asc())
        ).scalars().all()

    print()
    if lender is not None:
        print(
            f"Verification: lender={lender.name} (slug={lender.slug}, id={lender.id}), "
            f"client_id={client_id}"
        )
    else:
        print(f"Verification: client_id={client_id}")

    print(f"  Financial records: {len(rows)}")
    if rows:
        print(
            f"  Range: {rows[0].month:%Y-%m} .. {rows[-1].month:%Y-%m} "
            f"(status={rows[0].status})"
        )
        print(
            f"  Latest revenue: {rows[-1].revenue:,.2f} "
            f"({rows[-1].month:%Y-%m})"
        )

    expected = len(MONTHLY_REVENUE)
    if len(rows) < expected:
        print(f"  Warning: expected at least {expected} consecutive seed months.")


if __name__ == "__main__":
    seeded_client_id = seed_forecast_test_data()
    verify_seed(seeded_client_id)
