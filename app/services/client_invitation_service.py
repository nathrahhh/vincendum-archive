"""Create and manage client invitation tokens."""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.client_invitation import ClientInvitationORM
from app.models.user import UserORM

INVITATION_TTL_DAYS = 7


def generate_invitation_token() -> str:
    """Return a cryptographically secure URL-safe invitation token."""
    return secrets.token_urlsafe(32)


def hash_invitation_token(token: str) -> str:
    """Return a SHA-256 hex digest of the raw invitation token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_invitation_url(token: str) -> str:
    """Build a frontend invitation URL for development/testing."""
    base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/invite/{token}"


def normalize_invitation_email(email: str) -> str:
    return email.strip().lower()


def create_client_invitation(
    db: Session,
    *,
    client_id: int,
    lender_id: int,
    email: str,
) -> tuple[ClientInvitationORM, str]:
    """
    Create a pending invitation for ``email`` on an existing client.

    Returns ``(invitation, raw_token)``. The raw token is returned once for
    development; only ``token_hash`` is persisted.
    """
    client = db.execute(
        select(ClientORM).where(
            ClientORM.id == client_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client {client_id} not found",
        )

    normalized_email = normalize_invitation_email(email)
    if not normalized_email or "@" not in normalized_email:
        raise HTTPException(status_code=422, detail="Invalid email address")

    existing_pending = db.execute(
        select(ClientInvitationORM).where(
            ClientInvitationORM.client_id == client_id,
            ClientInvitationORM.lender_id == lender_id,
            func.lower(ClientInvitationORM.email) == normalized_email,
            ClientInvitationORM.status == "pending",
        )
    ).scalar_one_or_none()
    if existing_pending is not None:
        raise HTTPException(
            status_code=409,
            detail="A pending invitation already exists for this email and client",
        )

    raw_token = generate_invitation_token()
    now = datetime.now(timezone.utc)
    invitation = ClientInvitationORM(
        lender_id=lender_id,
        client_id=client_id,
        email=normalized_email,
        token_hash=hash_invitation_token(raw_token),
        status="pending",
        expires_at=now + timedelta(days=INVITATION_TTL_DAYS),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation, raw_token


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def accept_client_invitation(
    db: Session,
    *,
    auth0_user_id: str,
    email: str,
    raw_token: str,
) -> tuple[ClientInvitationORM, ClientORM, UserORM]:
    """
    Accept a pending invitation for an authenticated Auth0 identity.

    Creates or updates the local ``UserORM`` as a client user. ``client_id``
    and ``lender_id`` come only from the invitation row matched by token hash.
    """
    token = raw_token.strip()
    if not token:
        raise HTTPException(status_code=422, detail="Invitation token is required")

    invitation = db.execute(
        select(ClientInvitationORM).where(
            ClientInvitationORM.token_hash == hash_invitation_token(token),
        )
    ).scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    now = datetime.now(timezone.utc)
    if _as_utc(invitation.expires_at) <= now:
        if invitation.status == "pending":
            invitation.status = "expired"
            db.commit()
        raise HTTPException(status_code=410, detail="Invitation has expired")

    if invitation.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Invitation is {invitation.status}",
        )

    if normalize_invitation_email(email) != normalize_invitation_email(
        invitation.email,
    ):
        raise HTTPException(
            status_code=403,
            detail="Authenticated email does not match this invitation",
        )

    client = db.execute(
        select(ClientORM).where(ClientORM.id == invitation.client_id)
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    user = db.execute(
        select(UserORM).where(UserORM.auth0_user_id == auth0_user_id)
    ).scalar_one_or_none()

    if user is None:
        user = UserORM(
            email=normalize_invitation_email(email),
            auth0_user_id=auth0_user_id,
            role="client",
            lender_id=invitation.lender_id,
            client_id=invitation.client_id,
        )
        db.add(user)
    else:
        if (
            user.client_id is not None
            and user.client_id != invitation.client_id
        ):
            raise HTTPException(
                status_code=409,
                detail="User is already linked to a different client",
            )
        user.email = normalize_invitation_email(email)
        user.role = "client"
        user.client_id = invitation.client_id
        user.lender_id = invitation.lender_id

    invitation.status = "accepted"
    invitation.accepted_at = now

    db.commit()
    db.refresh(invitation)
    db.refresh(user)
    db.refresh(client)
    return invitation, client, user
