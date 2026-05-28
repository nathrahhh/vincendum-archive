from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BreachORM(Base):
    __tablename__ = "breaches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    limit_pct: Mapped[float] = mapped_column(Float, nullable=False)
    actual_pct: Mapped[float] = mapped_column(Float, nullable=False)
    detail: Mapped[str] = mapped_column(String(500), nullable=False)

