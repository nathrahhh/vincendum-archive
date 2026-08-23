from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.bank_connection import BankConnectionORM
    from app.models.bank_transaction import BankTransactionORM


class BankAccountORM(Base):
    """A bank account linked to a client's TrueLayer connection.

    Stores only the minimum account metadata needed by Vincendum.
    Does not store credentials, tokens, or account numbers.
    """

    __tablename__ = "bank_accounts"
    __table_args__ = (
        UniqueConstraint(
            "bank_connection_id",
            "truelayer_account_id",
            name="uq_bank_accounts_connection_truelayer_account",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    bank_connection_id: Mapped[int] = mapped_column(
        ForeignKey("bank_connections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    truelayer_account_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    account_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
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

    bank_connection: Mapped[BankConnectionORM] = relationship(
        back_populates="bank_accounts",
    )
    bank_transactions: Mapped[list[BankTransactionORM]] = relationship(
        back_populates="bank_account",
    )
