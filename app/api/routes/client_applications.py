from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.client import ClientORM
from app.models.position import PositionORM
from app.models.schemas import ClientApplicationCreate, Position
from app.services.concentration_risk_engine import RiskEngine

router = APIRouter(tags=["client-applications"])


@router.get("/client-applications")
def list_client_applications(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        text(
            "SELECT id, name, industry, credit_limit, status, created_at "
            "FROM client_applications ORDER BY created_at DESC"
        )
    ).mappings()
    return [dict(row) for row in rows.all()]


@router.post("/client-applications")
def create_client_application(
    payload: ClientApplicationCreate,
    db: Session = Depends(get_db),
) -> dict:
    application = db.execute(
        text(
            "INSERT INTO client_applications (name, industry, credit_limit, status) "
            "VALUES (:name, :industry, :credit_limit, :status) "
            "RETURNING id, name, industry, credit_limit, status"
        ),
        {
            "name": payload.name,
            "industry": payload.industry,
            "credit_limit": payload.credit_limit,
            "status": "pending",
        },
    ).mappings().one()
    db.commit()

    existing_positions = db.execute(select(PositionORM).order_by(PositionORM.name)).scalars().all()
    portfolio = [Position(name=p.name, value=p.value, industry=p.industry) for p in existing_positions]
    proposed_exposure = SimpleNamespace(
        name=payload.name,
        value=payload.credit_limit,
        industry=payload.industry,
    )
    risk_engine = RiskEngine()
    result = risk_engine.evaluate_deal(portfolio=portfolio, deal=proposed_exposure)

    if result.status.value == "REJECTED":
        application = db.execute(
            text(
                "UPDATE client_applications SET status = :status WHERE id = :id "
                "RETURNING id, name, industry, credit_limit, status"
            ),
            {"status": "rejected", "id": application["id"]},
        ).mappings().one()
        db.commit()
        reasons = risk_engine.get_breach_reasons(result.breaches)
        return {
            "message": "Application rejected due to concentration risk limits",
            "reasons": reasons,
            "application": dict(application),
        }

    application = db.execute(
        text(
            "UPDATE client_applications SET status = :status WHERE id = :id "
            "RETURNING id, name, industry, credit_limit, status"
        ),
        {"status": "pending", "id": application["id"]},
    ).mappings().one()
    db.commit()

    return {
        "message": "Application submitted for admin review",
        "application": dict(application),
    }


@router.post("/client-applications/{application_id}/approve")
def approve_client_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> dict:
    application = db.execute(
        text(
            "SELECT id, name, industry, credit_limit, status "
            "FROM client_applications WHERE id = :id"
        ),
        {"id": application_id},
    ).mappings().first()
    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found",
        )
    if application["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending applications can be approved",
        )

    client_row = ClientORM(
        name=application["name"],
        industry=application["industry"],
        credit_limit=application["credit_limit"],
    )
    db.add(client_row)
    db.execute(
        text("UPDATE client_applications SET status = :status WHERE id = :id"),
        {"status": "approved", "id": application_id},
    )
    db.commit()
    db.refresh(client_row)

    return {
        "message": "Client approved successfully",
        "client": {
            "id": client_row.id,
            "name": client_row.name,
            "industry": client_row.industry,
            "credit_limit": client_row.credit_limit,
        },
    }


@router.post("/client-applications/{application_id}/reject")
def reject_client_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> dict:
    application = db.execute(
        text(
            "SELECT id, name, industry, credit_limit, status "
            "FROM client_applications WHERE id = :id"
        ),
        {"id": application_id},
    ).mappings().first()
    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found",
        )
    if application["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending applications can be rejected",
        )

    application = db.execute(
        text(
            "UPDATE client_applications SET status = :status WHERE id = :id "
            "RETURNING id, name, industry, credit_limit, status, created_at"
        ),
        {"status": "rejected", "id": application_id},
    ).mappings().one()
    db.commit()

    return {
        "message": "Application rejected successfully",
        "application": dict(application),
    }
