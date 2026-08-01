from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.lender import LenderORM


# Platform user roles within a lender tenant.
# admin  — manage users, approve/reject applications, full tenant access
# analyst — evaluate deals, view clients/financials, submit risk checks
# viewer — read-only access within the lender tenant
USER_ROLES = ("admin", "analyst", "viewer")


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lender: Mapped[LenderORM] = relationship(back_populates="users")
