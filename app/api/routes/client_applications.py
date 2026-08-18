"""Client application HTTP routes (thin layer over the service)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client_application import ClientApplicationORM
from app.models.lender import LenderORM
from app.models.schemas import ClientApplicationCreate
from app.models.user import UserORM
from app.services.client_application_service import (
    accept_client_application as accept_client_application_service,
)
from app.services.client_application_service import (
    create_client_application as create_client_application_service,
)
from app.services.client_application_service import (
    list_client_applications as list_client_applications_service,
)
from app.services.client_application_service import (
    reject_client_application as reject_client_application_service,
)

router = APIRouter(tags=["client-applications"])


def _serialize_created_at(value: datetime) -> str:
    return value.isoformat()


def _application_to_dict(application: ClientApplicationORM) -> dict:
    return {
        "id": application.id,
        "lender_id": application.lender_id,
        "name": application.name,
        "industry": application.industry,
        "credit_limit": application.credit_limit,
        "registered_business_name": application.registered_business_name,
        "companies_house_number": application.companies_house_number,
        "incorporation_year": application.incorporation_year,
        "headcount": application.headcount,
        "revenue_last_fy": application.revenue_last_fy,
        "status": application.status,
        "created_at": _serialize_created_at(application.created_at),
    }


def _resolve_public_lender_id() -> int:
    """
    Resolve ``lender_id`` from the public lender URL/slug context.

    Not implemented: ``LenderORM`` has no slug field, and there is no
    existing FastAPI dependency that maps a public lender context to an id.
    Do not invent one here.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Public lender context dependency is not available. "
            "Unauthenticated application submission requires a "
            "lender-specific public route/slug that resolves to lender_id."
        ),
    )


@router.get("/client-applications")
def list_client_applications(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> list[dict]:
    """List applications for the authenticated admin's lender."""
    lender_id = get_user_lender_id(current_user)
    applications = list_client_applications_service(
        db,
        lender_id=lender_id,
    )
    return [_application_to_dict(application) for application in applications]


@router.post("/client-applications")
def create_client_application(
    payload: ClientApplicationCreate,
    db: Session = Depends(get_db),
) -> dict:
    """
    Public application submission.

    No authenticated client user is required. ``lender_id`` must come from
    the public lender context (not yet wired in this codebase).
    """
    lender_id = _resolve_public_lender_id()
    application = create_client_application_service(
        db,
        lender_id=lender_id,
        payload=payload,
    )
    return {
        "message": "Application submitted for admin review",
        "application": _application_to_dict(application),
    }


@router.post("/client-applications/public/{slug}")
def create_public_client_application(
    slug: str,
    payload: ClientApplicationCreate,
    db: Session = Depends(get_db),
) -> dict:
    """
    Public application submission for a lender identified by slug.

    ``lender_id`` comes from the URL slug, not the request body.
    """
    lender = db.execute(
        select(LenderORM).where(LenderORM.slug == slug)
    ).scalar_one_or_none()
    if lender is None:
        raise HTTPException(
            status_code=404,
            detail=f"Lender with slug '{slug}' not found",
        )

    application = create_client_application_service(
        db,
        lender_id=lender.id,
        payload=payload,
    )
    return {
        "message": "Application submitted for admin review",
        "application": _application_to_dict(application),
    }


@router.post("/client-applications/{application_id}/approve")
def approve_client_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> dict:
    """Accept a pending application and create the client record."""
    lender_id = get_user_lender_id(current_user)
    client, application = accept_client_application_service(
        db,
        application_id,
        lender_id=lender_id,
    )
    return {
        "message": "Client approved successfully",
        "client": {
            "id": client.id,
            "name": client.name,
            "industry": client.industry,
            "credit_limit": client.credit_limit,
        },
        "application": _application_to_dict(application),
    }


@router.post("/client-applications/{application_id}/reject")
def reject_client_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> dict:
    """Reject a pending application owned by the authenticated lender."""
    lender_id = get_user_lender_id(current_user)
    application = reject_client_application_service(
        db,
        application_id,
        lender_id=lender_id,
    )
    return {
        "message": "Application rejected successfully",
        "application": _application_to_dict(application),
    }
