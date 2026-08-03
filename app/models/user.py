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
# admin  — lender staff; always tied to a lender tenant
# client — borrower applicant; may exist before a lender assigns them
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
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Nullable so client users can register via Auth0 before a lender approves
    # and assigns them to a tenant. Admin users should always have a lender_id.
    lender_id: Mapped[int | None] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lender: Mapped[LenderORM | None] = relationship(back_populates="users")
    # Present for role=client users once a ClientORM profile is linked.
    client: Mapped[ClientORM | None] = relationship(
        back_populates="user",
        uselist=False,
    )
