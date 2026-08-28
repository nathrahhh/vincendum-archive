from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.repayment import RepaymentORM


class DealORM(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    principal_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    interest_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    interest_rate_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="fixed",
        server_default="fixed",
    )

    repayment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="amortizing",
        server_default="amortizing",
    )


    term_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    maturity_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    payment_frequency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default="monthly",
        server_default="monthly",
    )

    first_payment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    client: Mapped[ClientORM] = relationship()
    repayments: Mapped[list[RepaymentORM]] = relationship(
        back_populates="deal",
    )
