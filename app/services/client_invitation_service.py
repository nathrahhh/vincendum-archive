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
