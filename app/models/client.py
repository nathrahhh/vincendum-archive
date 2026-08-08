
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.lender import LenderORM
    from app.models.user import UserORM


class ClientORM(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    industry: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    credit_limit: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Nullable initially so existing production rows remain valid
    # until backfilled.
    lender_id: Mapped[int | None] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=True,
        index=True,
    )

    lender: Mapped[LenderORM | None] = relationship(
        back_populates="clients",
    )

    # Multiple users can belong to the same client.
    users: Mapped[list[UserORM]] = relationship(
        back_populates="client",
    )
