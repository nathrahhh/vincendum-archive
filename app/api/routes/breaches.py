import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.breach import BreachORM
from app.models.user import UserORM
from app.services.breach_helpers import industry_for_rule, reason_for_rule

logger = logging.getLogger(__name__)

router = APIRouter(tags=["breaches"])

BreachPayload = dict[str, float | int | str | None]


def _serialize_breach(breach: BreachORM) -> BreachPayload:
    return {
        "id": breach.id,
        "client_id": breach.client_id,
        "reason": breach.reason or reason_for_rule(breach.rule, breach.detail),
        "rule": breach.rule,
        "threshold": breach.threshold,
        "actual_value": breach.actual_value,
        "detail": breach.detail,
        "status": breach.status,
    }


def _industry_key(breach: BreachORM) -> str:
    return (
        breach.industry
        or industry_for_rule(breach.rule, breach.industry)
        or "Unknown"
    )


@router.get("/breaches")
def list_breaches(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> dict[str, list[BreachPayload]]:
    """
    List breaches for lender staff, grouped by industry.

    Tenant isolation: only breaches for the authenticated admin's lender.
    """
    lender_id = get_user_lender_id(current_user)
    rows = db.execute(
        select(BreachORM)
        .where(BreachORM.lender_id == lender_id)
        .order_by(BreachORM.id.desc())
    ).scalars().all()
    logger.info("list_breaches fetched row_count=%d lender_id=%s", len(rows), lender_id)

    grouped: dict[str, list[BreachPayload]] = {}
    for breach in rows:
        industry_key = _industry_key(breach)
        logger.debug(
            "list_breaches id=%s industry=%r reason=%r rule=%s status=%s",
            breach.id,
            industry_key,
            breach.reason or reason_for_rule(breach.rule, breach.detail),
            breach.rule,
            breach.status,
        )
        grouped.setdefault(industry_key, []).append(_serialize_breach(breach))

    logger.info("list_breaches grouped_industries=%s", list(grouped.keys()))
    return grouped


@router.post("/breaches/{breach_id}/resolve")
def resolve_breach(
    breach_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> BreachPayload:
    """Resolve an OPEN breach for the authenticated admin's lender."""
    lender_id = get_user_lender_id(current_user)
    breach = db.execute(
        select(BreachORM).where(
            BreachORM.id == breach_id,
            BreachORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if breach is None:
        raise HTTPException(status_code=404, detail=f"Breach {breach_id} not found")

    if breach.status != "OPEN":
        raise HTTPException(
            status_code=400,
            detail=f"Breach {breach_id} is not open",
        )

    breach.status = "RESOLVED"
    breach.resolved_by = current_user.id
    breach.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(breach)
    return _serialize_breach(breach)
