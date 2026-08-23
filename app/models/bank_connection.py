from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.bank_account import BankAccountORM
    from app.models.client import ClientORM


class BankConnectionORM(Base):
    """A client's authorised TrueLayer Data V3 bank connection."""

    __tablename__ = "bank_connections"
    __table_args__ = (
        UniqueConstraint(
            "truelayer_connection_id",
            name="uq_bank_connections_truelayer_connection_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    truelayer_connection_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Unguessable correlator placed on our return_uri so the public callback
    # can locate this row without trusting a browser-supplied client_id.
    # TrueLayer Data V3 does not document return_uri query parameters.
    callback_state: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
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

    client: Mapped[ClientORM] = relationship(
        back_populates="bank_connections",
    )
    bank_accounts: Mapped[list[BankAccountORM]] = relationship(
        back_populates="bank_connection",
    )
