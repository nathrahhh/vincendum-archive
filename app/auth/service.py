"""Auth0 token verification and user lookup placeholders."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import UserORM


def verify_auth0_token(token: str) -> dict:
    """
    Verify an Auth0-issued JWT and return its claims.

    Future implementation:
    - Validate signature against Auth0 JWKS
    - Check issuer, audience, expiry
    - Return decoded claims (including ``sub``)

    The JWT ``sub`` claim maps to ``users.auth0_user_id``.
    """
    # TODO: Implement Auth0 JWT verification.
    raise NotImplementedError("Auth0 JWT verification is not implemented yet.")


def get_user_by_auth0_id(db: Session, auth0_user_id: str) -> UserORM | None:
    """
    Load a local user by Auth0 subject identifier.

    Future implementation:
    - Query ``UserORM`` where ``auth0_user_id == auth0_user_id``
      (the Auth0 JWT ``sub`` claim)
    - Return ``None`` when no matching user exists
    """
    # TODO: Implement database lookup by users.auth0_user_id.
    raise NotImplementedError("Auth0 user lookup is not implemented yet.")
