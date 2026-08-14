from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.client_application import ClientApplicationORM
    from app.models.lender import LenderORM


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_applications.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="s3",
        server_default="s3",
    )

    storage_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    external_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    lender: Mapped[LenderORM] = relationship(
        back_populates="documents",
    )
    client: Mapped[ClientORM | None] = relationship(
        back_populates="documents",
    )
    application: Mapped[ClientApplicationORM | None] = relationship(
        back_populates="documents",
    )
