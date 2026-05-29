import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.breach import BreachORM
from app.services.breach_helpers import resolve_breach_industry, resolve_breach_reason

logger = logging.getLogger(__name__)

router = APIRouter(tags=["breaches"])


@router.get("/breaches")
def list_breaches(db: Session = Depends(get_db)) -> dict[str, list[dict[str, float | int | str]]]:
    rows = db.execute(select(BreachORM).order_by(BreachORM.id.desc())).scalars().all()
    logger.info("list_breaches fetched row_count=%d", len(rows))

    grouped: dict[str, list[dict[str, float | int | str]]] = {}
    for breach in rows:
        industry_key = resolve_breach_industry(breach)
        reason = resolve_breach_reason(breach)
        logger.debug(
            "list_breaches parsing id=%s raw_industry=%r raw_reason=%r resolved_industry=%s resolved_reason=%s rule=%s",
            breach.id,
            breach.industry,
            breach.reason,
            industry_key,
            reason,
            breach.rule,
        )
        grouped.setdefault(industry_key, []).append(
            {
                "id": breach.id,
                "reason": reason,
                "rule": breach.rule,
                "limit_pct": breach.limit_pct,
                "actual_pct": breach.actual_pct,
                "detail": breach.detail,
            }
        )

    logger.info("list_breaches grouped_industries=%s", list(grouped.keys()))
    return grouped
