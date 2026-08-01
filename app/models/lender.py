from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import ClientORM
    from app.models.client_application import ClientApplicationORM
    from app.models.user import UserORM


class LenderORM(Base):
    __tablename__ = "lenders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    users: Mapped[list[UserORM]] = relationship(back_populates="lender")
    clients: Mapped[list[ClientORM]] = relationship(back_populates="lender")
    client_applications: Mapped[list[ClientApplicationORM]] = relationship(
        back_populates="lender",
    )
