from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.audit_log import AuditLogORM
from app.models.schemas import AuditLogRecord
from app.models.user import UserORM

router = APIRouter(tags=["audit-logs"])


@router.get("/audit-logs", response_model=list[AuditLogRecord])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[AuditLogRecord]:
    """Return audit logs for the authenticated admin's lender, newest first."""
    lender_id = get_user_lender_id(current_user)
    rows = db.execute(
        select(AuditLogORM)
        .where(AuditLogORM.lender_id == lender_id)
        .order_by(AuditLogORM.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [AuditLogRecord.model_validate(row) for row in rows]
