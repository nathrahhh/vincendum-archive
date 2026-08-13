from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BreachORM(Base):
    __tablename__ = "breaches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    rule: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    industry: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    actual_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    detail: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
        index=True,
    )

    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )