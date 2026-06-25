from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import ClientFinancialCreate

router = APIRouter(tags=["client-financials"])


def _serialize_record(row: object) -> dict:
    record = dict(row)  # type: ignore[arg-type]
    month = record.get("month")
    if hasattr(month, "isoformat"):
        record["month"] = month.isoformat()  # type: ignore[union-attr]
    return record


@router.post("/client-financials")
def create_client_financial(
    payload: ClientFinancialCreate,
    db: Session = Depends(get_db),
) -> dict:
    client = db.execute(
        text("SELECT id FROM clients WHERE id = :client_id"),
        {"client_id": payload.client_id},
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {payload.client_id} not found")

    existing = db.execute(
        text(
            "SELECT id FROM client_financials "
            "WHERE client_id = :client_id AND month = :month"
        ),
        {"client_id": payload.client_id, "month": payload.month},
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Financial record already exists for client {payload.client_id} and month {payload.month}",
        )

    row = db.execute(
        text(
            "INSERT INTO client_financials "
            "(client_id, month, revenue, cogs, opex, cash_balance) "
            "VALUES (:client_id, :month, :revenue, :cogs, :opex, :cash_balance) "
            "RETURNING id, client_id, month, revenue, cogs, opex, cash_balance"
        ),
        {
            "client_id": payload.client_id,
            "month": payload.month,
            "revenue": payload.revenue,
            "cogs": payload.cogs,
            "opex": payload.opex,
            "cash_balance": payload.cash_balance,
        },
    ).mappings().one()
    db.commit()

    return {
        "message": "Financial data added successfully",
        "record": _serialize_record(row),
    }
