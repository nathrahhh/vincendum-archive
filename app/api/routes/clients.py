from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.client import ClientORM
from app.models.schemas import ClientCreditLimitUpdate
from app.services.client_exposure_service import get_client_exposure

router = APIRouter(prefix="/clients", tags=["clients"])


def _client_to_dict(client: ClientORM) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "industry": client.industry,
        "credit_limit": client.credit_limit,
    }


@router.get("")
def list_clients(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(ClientORM).order_by(ClientORM.id.asc())).scalars().all()
    return [_client_to_dict(row) for row in rows]


@router.get("/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(ClientORM, client_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    exposure = get_client_exposure(db, client_id)
    return {**_client_to_dict(row), **exposure}


@router.put("/{client_id}/credit-limit")
def update_client_credit_limit(
    client_id: int,
    payload: ClientCreditLimitUpdate,
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(ClientORM, client_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    row.credit_limit = payload.credit_limit
    db.commit()
    db.refresh(row)
    return _client_to_dict(row)
