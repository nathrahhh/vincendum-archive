"""Role-based authorization dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.user import UserORM


def require_admin(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """
    Allow the request only when the current user has role ``admin``.

    Example::

        current_user: UserORM = Depends(require_admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


def require_client(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """
    Allow the request only when the current user has role ``client``.

    Example::

        current_user: UserORM = Depends(require_client)
    """
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required",
        )
    return current_user
