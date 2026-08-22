from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.deal import DealORM


class RepaymentORM(Base):
    __tablename__ = "repayments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    deal_id: Mapped[int] = mapped_column(
        ForeignKey("deals.id"),
        nullable=False,
        index=True,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    principal_due: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    interest_due: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    total_due: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    principal_paid: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
        server_default="0",
    )

    interest_paid: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
        server_default="0",
    )

    total_paid: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
        server_default="0",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SCHEDULED",
        server_default="SCHEDULED",
    )

    paid_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    deal: Mapped[DealORM] = relationship(
        back_populates="repayments",
    )
