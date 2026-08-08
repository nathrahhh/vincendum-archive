
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.lender import LenderORM


# Application roles (Auth0 / JWT claims should use these values).
#
# admin  — lender staff; tied to a lender tenant
# client — borrower/client user; tied to a client profile
USER_ROLES = ("admin", "client")


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Auth0 subject identifier (sub). Passwords are not stored locally.
    auth0_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Lender tenant this user belongs to.
    # Nullable because a user may not yet be assigned to a lender.
    lender_id: Mapped[int | None] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=True,
        index=True,
    )

    # Client this user belongs to.
    # Multiple users can belong to the same client.
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lender: Mapped[LenderORM | None] = relationship(
        back_populates="users",
    )

    client: Mapped[ClientORM | None] = relationship(
        back_populates="users",
    )
