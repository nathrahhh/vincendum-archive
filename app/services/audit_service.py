from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLogORM


def record_audit_event(
    db: Session,
    *,
    lender_id: int,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    changes: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogORM:
    """
    Persist an audit event on ``db`` without committing.

    The caller's transaction controls commit/rollback so the business
    operation and its audit record succeed or fail together.
    """
    audit_log = AuditLogORM(
        lender_id=lender_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        metadata_=metadata,
    )
    db.add(audit_log)
    return audit_log
