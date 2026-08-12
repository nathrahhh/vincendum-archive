from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.schemas import (
    ClientFinancialCreate,
    ClientFinancialRecord,
    ClientFinancialResponse,
)
from app.models.user import UserORM
from app.services.client_financial_service import (
    approve_client_financial as approve_client_financial_service,
)
from app.services.client_financial_service import (
    reject_client_financial as reject_client_financial_service,
)

router = APIRouter(tags=["client-financials"])


def _financial_for_lender(
    db: Session,
    financial_id: int,
    lender_id: int,
) -> ClientFinancialORM | None:
    return db.execute(
        select(ClientFinancialORM)
        .join(ClientORM, ClientFinancialORM.client_id == ClientORM.id)
        .where(
            ClientFinancialORM.id == financial_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()


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


@router.post("/client/me/financials")
def create_my_client_financial(
    payload: ClientFinancialCreate,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> dict:
    """
    Submit a new PENDING financial record for the authenticated client.

    ``client_id`` is taken only from the authenticated client profile.
    """
    existing = db.execute(
        select(ClientFinancialORM).where(
            ClientFinancialORM.client_id == current_client.id,
            ClientFinancialORM.month == payload.month,
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Financial record already exists for client {current_client.id} "
                f"and month {payload.month}"
            ),
        )

    row = ClientFinancialORM(
        client_id=current_client.id,
        month=payload.month,
        revenue=payload.revenue,
        cogs=payload.cogs,
        gross_profit=payload.gross_profit,
        opex=payload.opex,
        cash_balance=payload.cash_balance,
        status="PENDING",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Financial data added successfully",
        "record": _to_record(row).model_dump(mode="json"),
    }


@router.post(
    "/client-financials/{id}/approve",
    response_model=ClientFinancialRecord,
)
def approve_client_financial(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> ClientFinancialRecord:
    """Approve a pending client financial submission."""
    lender_id = get_user_lender_id(current_user)
    row = _financial_for_lender(db, id, lender_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client financial {id} not found")
    return approve_client_financial_service(db, id)


@router.post(
    "/client-financials/{id}/reject",
    response_model=ClientFinancialRecord,
)
def reject_client_financial(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> ClientFinancialRecord:
    """Reject a pending client financial submission."""
    lender_id = get_user_lender_id(current_user)
    row = _financial_for_lender(db, id, lender_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client financial {id} not found")
    return reject_client_financial_service(db, id)


@router.get("/clients/{client_id}/financials", response_model=ClientFinancialResponse)
def list_client_financials(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
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


@router.get("/client/me/financials", response_model=ClientFinancialResponse)
def list_my_client_financials(
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> ClientFinancialResponse:
    rows = db.execute(
        select(ClientFinancialORM)
        .where(ClientFinancialORM.client_id == current_client.id)
        .order_by(ClientFinancialORM.month.asc())
    ).scalars().all()

    return ClientFinancialResponse(
        client_id=current_client.id,
        historical=[_to_record(row) for row in rows],
    )
