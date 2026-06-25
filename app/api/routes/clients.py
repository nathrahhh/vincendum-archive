from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("")
def list_clients(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        text("SELECT id, name, industry, credit_limit FROM clients ORDER BY id ASC")
    ).mappings()
    return [dict(row) for row in rows.all()]


@router.get("/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        text(
            "SELECT id, name, industry, credit_limit FROM clients WHERE id = :client_id"
        ),
        {"client_id": client_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return dict(row)
