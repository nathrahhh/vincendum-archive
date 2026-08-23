from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.bank_account import BankAccountORM


class BankTransactionORM(Base):
    """A bank transaction linked to a client's TrueLayer bank account.

    Ownership is inherited via BankAccount → BankConnection → Client.
    Does not store credentials, tokens, or account identifiers.
    """

    __tablename__ = "bank_transactions"
    __table_args__ = (
        UniqueConstraint(
            "bank_account_id",
            "truelayer_transaction_id",
            name="uq_bank_transactions_account_truelayer_transaction",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    truelayer_transaction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # TrueLayer exposes a single ``timestamp``; stored as booking_date.
    booking_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Not present on the current TrueLayerClient transaction model.
    value_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    # Mapped from TrueLayer transaction ``status`` (e.g. booked / pending).
    transaction_type: Mapped[str | None] = mapped_column(
        String(50),
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

    bank_account: Mapped[BankAccountORM] = relationship(
        back_populates="bank_transactions",
    )
