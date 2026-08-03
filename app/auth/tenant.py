"""Multi-tenant (lender) authorization helpers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.user import UserORM


def get_user_lender_id(current_user: UserORM) -> int:
    """
    Return the lender tenant id for ``current_user``.

    Raises:
        HTTPException: 403 when the user is not assigned to a lender.
    """
    if current_user.lender_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a lender",
        )
    return current_user.lender_id


def require_lender_user(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """
    Allow the request only when the current user belongs to a lender tenant.

    Typical usage in routes::

        current_user: UserORM = Depends(require_lender_user)
        lender_id = get_user_lender_id(current_user)
    """
    get_user_lender_id(current_user)
    return current_user
