"""Client application lifecycle service.

Public borrowers submit applications under a lender-specific public context
that supplies ``lender_id``. Lenders list, accept, or reject applications
scoped to their own tenant. Concentration-risk evaluation is intentionally
omitted from this workflow.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.client_application import ClientApplicationORM
from app.models.schemas import ClientApplicationCreate
from app.services.documents.document_service import (
    assign_application_documents_to_client,
)


def _get_application_or_404(
    db: Session,
    application_id: int,
    *,
    lender_id: int,
) -> ClientApplicationORM:
    application = db.execute(
        select(ClientApplicationORM).where(
            ClientApplicationORM.id == application_id,
            ClientApplicationORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found",
        )
    return application


def create_client_application(
    db: Session,
    *,
    lender_id: int,
    payload: ClientApplicationCreate,
) -> ClientApplicationORM:
    """
    Persist a new pending application for ``lender_id``.

    ``lender_id`` comes from the public lender route/context, not the payload.
    """
    application = ClientApplicationORM(
        lender_id=lender_id,
        name=payload.name,
        industry=payload.industry,
        credit_limit=payload.credit_limit,
        registered_business_name=payload.registered_business_name,
        companies_house_number=payload.companies_house_number,
        incorporation_year=payload.incorporation_year,
        headcount=payload.headcount,
        revenue_last_fy=payload.revenue_last_fy,
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_client_applications(
    db: Session,
    *,
    lender_id: int,
) -> list[ClientApplicationORM]:
    """Return applications owned by ``lender_id``, newest first."""
    return list(
        db.execute(
            select(ClientApplicationORM)
            .where(ClientApplicationORM.lender_id == lender_id)
            .order_by(ClientApplicationORM.created_at.desc())
        ).scalars().all()
    )


def accept_client_application(
    db: Session,
    application_id: int,
    *,
    lender_id: int,
) -> tuple[ClientORM, ClientApplicationORM]:
    """
    Accept a pending application and create the corresponding ``ClientORM``.

    Business-profile fields stay on the application; they are not copied to
    the client record. Application-owned documents for this lender are
    reassigned to the new client in the same transaction.
    """
    application = _get_application_or_404(
        db,
        application_id,
        lender_id=lender_id,
    )
    if application.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending applications can be approved",
        )

    client = ClientORM(
        name=application.name,
        industry=application.industry,
        credit_limit=application.credit_limit,
        lender_id=application.lender_id,
    )
    db.add(client)
    db.flush()

    application.status = "approved"

    assign_application_documents_to_client(
        db,
        lender_id=lender_id,
        application_id=application.id,
        client_id=client.id,
    )

    db.commit()
    db.refresh(client)
    db.refresh(application)
    return client, application


def reject_client_application(
    db: Session,
    application_id: int,
    *,
    lender_id: int,
) -> ClientApplicationORM:
    """Reject a pending application owned by ``lender_id``."""
    application = _get_application_or_404(
        db,
        application_id,
        lender_id=lender_id,
    )
    if application.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending applications can be rejected",
        )

    application.status = "rejected"
    db.commit()
    db.refresh(application)
    return application
