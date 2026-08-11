"""Client-role identity dependency (UserORM → ClientORM)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.user import UserORM


def get_current_client(
    current_user: UserORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientORM:
    """
    Resolve the ``ClientORM`` profile for the authenticated client user.

    Example::

        current_client: ClientORM = Depends(get_current_client)
    """
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required",
        )

    if current_user.client_id is None or current_user.lender_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No client profile is linked to this user",
        )

    client = db.execute(
        select(ClientORM).where(
            ClientORM.id == current_user.client_id,
            ClientORM.lender_id == current_user.lender_id,
        )
    ).scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No client profile is linked to this user",
        )

    return client
