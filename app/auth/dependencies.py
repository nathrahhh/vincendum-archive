"""FastAPI dependencies for resolving the authenticated user."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import UserORM


def get_current_user(db: Session = Depends(get_db)) -> UserORM:
    """
    Resolve the authenticated ``UserORM`` for the current request.

    Future Auth0 flow (replace this placeholder body only):
    1. Read the Bearer token from the ``Authorization`` header
    2. ``claims = verify_auth0_token(token)``  # app.auth.service
    3. ``user = get_user_by_auth0_id(db, claims["sub"])``  # maps JWT sub → auth0_user_id
    4. Raise HTTP 401 if the token is invalid or the user is missing
    5. Return the ``UserORM``

    Example::

        current_user: UserORM = Depends(get_current_user)
    """
    # db will be used for get_user_by_auth0_id once Auth0 is wired.
    _ = db

    # Placeholder identity until Auth0 JWT extraction/verification is wired.
    return UserORM(
    id=1,
    email="test@example.com",
    auth0_user_id="auth0|placeholder",
    role="admin",
    lender_id=1,
    )
