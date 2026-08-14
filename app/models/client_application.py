from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.document import DocumentORM
    from app.models.lender import LenderORM


class ClientApplicationORM(Base):
    __tablename__ = "client_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=False,
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

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lender: Mapped[LenderORM] = relationship(
        back_populates="client_applications",
    )
    documents: Mapped[list[DocumentORM]] = relationship(
        back_populates="application",
    )