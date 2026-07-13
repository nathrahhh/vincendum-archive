from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.schemas import (
    ClientFinancialCreate,
    ClientFinancialRecord,
    ClientFinancialResponse,
)

router = APIRouter(tags=["client-financials"])


def _to_record(row: ClientFinancialORM) -> ClientFinancialRecord:
    return ClientFinancialRecord(
        id=row.id,
        client_id=row.client_id,
        month=row.month,
        revenue=row.revenue,
        cogs=row.cogs,
        gross_profit=row.gross_profit,
        opex=row.opex,
        cash_balance=row.cash_balance,
    )


@router.post("/client-financials")
def create_client_financial(
    payload: ClientFinancialCreate,
    db: Session = Depends(get_db),
) -> dict:
    client = db.get(ClientORM, payload.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {payload.client_id} not found")

    existing = db.execute(
        select(ClientFinancialORM).where(
            ClientFinancialORM.client_id == payload.client_id,
            ClientFinancialORM.month == payload.month,
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Financial record already exists for client {payload.client_id} "
                f"and month {payload.month}"
            ),
        )

    row = ClientFinancialORM(
        client_id=payload.client_id,
        month=payload.month,
        revenue=payload.revenue,
        cogs=payload.cogs,
        gross_profit=payload.gross_profit,
        opex=payload.opex,
        cash_balance=payload.cash_balance,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Financial data added successfully",
        "record": _to_record(row).model_dump(mode="json"),
    }


@router.get("/clients/{client_id}/financials", response_model=ClientFinancialResponse)
def list_client_financials(
    client_id: int,
    db: Session = Depends(get_db),
) -> ClientFinancialResponse:
    rows = db.execute(
        select(ClientFinancialORM)
        .where(ClientFinancialORM.client_id == client_id)
        .order_by(ClientFinancialORM.month.asc())
    ).scalars().all()

    return ClientFinancialResponse(
        client_id=client_id,
        historical=[_to_record(row) for row in rows],
    )
