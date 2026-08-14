import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_financial import ClientFinancialORM
from app.models.schemas import ClientFinancialRecord
from app.services.audit_service import record_audit_event
from app.services.breaches.financial_breach_service import (
    evaluate_and_persist_financial_breach,
)

logger = logging.getLogger(__name__)


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


def approve_client_financial(
    db: Session,
    financial_id: int,
    *,
    lender_id: int,
    user_id: int,
) -> ClientFinancialRecord:
    row = _get_financial_or_404(db, financial_id)
    if row.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Client financial {financial_id} is not pending",
        )

    previous_status = row.status
    row.status = "APPROVED"
    logger.info(
        "approve_client_financial financial_id=%s client_id=%s lender_id=%s "
        "previous_status=%s new_status=%s",
        row.id,
        row.client_id,
        lender_id,
        previous_status,
        row.status,
    )
    db.flush()
    print("pls work")
    logger.info(
        "approve_client_financial starting breach evaluation "
        "financial_id=%s client_id=%s lender_id=%s",
        row.id,
        row.client_id,
        lender_id,
    )
    breach = evaluate_and_persist_financial_breach(
        db,
        lender_id=lender_id,
        client_id=row.client_id,
        financial_id=row.id,
    )
    logger.info(
        "approve_client_financial breach evaluation complete "
        "financial_id=%s client_id=%s breach_created=%s breach_id=%s",
        row.id,
        row.client_id,
        breach is not None,
        getattr(breach, "id", None),
    )
    record_audit_event(
        db,
        lender_id=lender_id,
        user_id=user_id,
        action="client_financial.approved",
        resource_type="client_financial",
        resource_id=row.id,
    )
    print("yeay")
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
