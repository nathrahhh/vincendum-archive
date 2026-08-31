from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.lender import LenderORM


class PortfolioORM(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    lender_id: Mapped[int] = mapped_column(
        ForeignKey("lenders.id"),
        nullable=False,
        index=True,
    )

    capital_allocation: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    lender: Mapped[LenderORM] = relationship(
        back_populates="portfolios",
    )
    clients: Mapped[list[ClientORM]] = relationship(
        back_populates="portfolio",
    )
