from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.deal import DealORM


class PositionORM(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    deal_id: Mapped[int] = mapped_column(
        ForeignKey("deals.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    deal: Mapped[DealORM] = relationship(
        back_populates="position",
    )
