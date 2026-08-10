"""FastAPI dependencies for resolving the authenticated user."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.service import Auth0TokenError, get_user_by_auth0_id, verify_auth0_token
from app.db import get_db
from app.models.user import UserORM

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedAuth0Identity:
    """Verified Auth0 identity without local user provisioning."""

    auth0_user_id: str
    email: str


def _email_from_claims(claims: dict) -> str | None:
    email = claims.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip()

    # Custom namespaced claim sometimes used on Auth0 access tokens.
    for key, value in claims.items():
        if key.endswith("/email") and isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _require_bearer_claims(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_auth0_token(credentials.credentials)
        print("AUTH0 CLAIMS:", claims)
    except Auth0TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return claims


def get_authenticated_auth0_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedAuth0Identity:
    """
    Verify the Auth0 access token and return ``sub`` + email.

    Does **not** create or update a local ``UserORM``. Use this for flows
    (such as invitation acceptance) that must assign role/tenant themselves.
    """
    claims = _require_bearer_claims(credentials)

    auth0_user_id = claims.get("sub")
    if not isinstance(auth0_user_id, str) or not auth0_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth0 token missing sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = _email_from_claims(claims)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth0 token missing email claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedAuth0Identity(
        auth0_user_id=auth0_user_id.strip(),
        email=email,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> UserORM:
    """
    Resolve the authenticated ``UserORM`` for the current request.

    Flow:
    1. Read the Bearer token from the ``Authorization`` header
    2. ``claims = verify_auth0_token(token)``
    3. Look up ``users.auth0_user_id == claims["sub"]``
    4. Provision a local admin user on first login if missing
    5. Return the ``UserORM``

    Example::

        current_user: UserORM = Depends(get_current_user)
    """
    claims = _require_bearer_claims(credentials)

    auth0_user_id = claims.get("sub")
    if not isinstance(auth0_user_id, str) or not auth0_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth0 token missing sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = _email_from_claims(claims)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth0 token missing email claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_auth0_id(db, auth0_user_id)

    if user is not None:
        return user

    # First-login provisioning for lender staff (admin) only.
    user = UserORM(
        email=email,
        auth0_user_id=auth0_user_id,
        role="admin",
        lender_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
