from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_financial import ClientFinancialORM
from app.models.schemas import ClientFinancialRecord


def _get_financial_or_404(db: Session, financial_id: int) -> ClientFinancialORM:
    row = db.execute(
        select(ClientFinancialORM).where(ClientFinancialORM.id == financial_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client financial {financial_id} not found",
        )
    return row


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
        status=row.status,
    )


def approve_client_financial(db: Session, financial_id: int) -> ClientFinancialRecord:
    row = _get_financial_or_404(db, financial_id)
    if row.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Client financial {financial_id} is not pending",
        )

    row.status = "APPROVED"
    db.commit()
    db.refresh(row)
    return _to_record(row)


def reject_client_financial(db: Session, financial_id: int) -> ClientFinancialRecord:
    row = _get_financial_or_404(db, financial_id)
    if row.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Client financial {financial_id} is not pending",
        )

    row.status = "REJECTED"
    db.commit()
    db.refresh(row)
    return _to_record(row)
