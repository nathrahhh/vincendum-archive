"""Auth0 JWT verification and local user lookup."""

from __future__ import annotations

import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserORM


class Auth0TokenError(Exception):
    """Raised when an Auth0 access token cannot be verified."""


def _auth0_domain() -> str:
    domain = (
        os.getenv("AUTH0_DOMAIN")
        or os.getenv("VITE_AUTH0_DOMAIN")
        or ""
    ).strip()
    if not domain:
        raise Auth0TokenError("AUTH0_DOMAIN is not configured")
    return domain.rstrip("/")


def _auth0_audience() -> str:
    audience = (
        os.getenv("AUTH0_AUDIENCE")
        or os.getenv("AUTH0_API_AUDIENCE")
        or ""
    ).strip()
    if not audience:
        raise Auth0TokenError("AUTH0_AUDIENCE is not configured")
    return audience


def _auth0_issuer() -> str:
    configured = os.getenv("AUTH0_ISSUER", "").strip()
    if configured:
        return configured if configured.endswith("/") else f"{configured}/"
    return f"https://{_auth0_domain()}/"


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    jwks_url = f"https://{_auth0_domain()}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def verify_auth0_token(token: str) -> dict:
    """
    Verify an Auth0-issued JWT and return its claims.

    Validates:
    - RS256 signature against Auth0 JWKS
    - issuer
    - audience
    - expiry

    The JWT ``sub`` claim maps to ``users.auth0_user_id``.
    """
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_auth0_audience(),
            issuer=_auth0_issuer(),
            options={
                "require": ["exp", "iss", "aud", "sub"],
            },
        )
    except Auth0TokenError:
        raise
    except Exception as exc:
        raise Auth0TokenError(f"Invalid Auth0 token: {exc}") from exc

    if not isinstance(claims, dict):
        raise Auth0TokenError("Invalid Auth0 token claims")

    return claims


def get_user_by_auth0_id(db: Session, auth0_user_id: str) -> UserORM | None:
    """Load a local user by Auth0 subject identifier (``users.auth0_user_id``)."""
    return db.execute(
        select(UserORM).where(UserORM.auth0_user_id == auth0_user_id)
    ).scalar_one_or_none()
