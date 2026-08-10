from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.lender import LenderORM


# Invitation lifecycle statuses.
INVITATION_STATUSES = ("pending", "accepted", "expired", "cancelled")


class ClientInvitationORM(Base):
    __tablename__ = "client_invitations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=False,
        index=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Store only a hash of the invitation token, never the raw token.
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        server_default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lender: Mapped[LenderORM] = relationship(
        back_populates="client_invitations",
    )
    client: Mapped[ClientORM] = relationship(
        back_populates="invitations",
    )
