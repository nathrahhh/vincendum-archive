from datetime import date

from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClientFinancialORM(Base):
    __tablename__ = "client_financials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    revenue: Mapped[float] = mapped_column(Float, nullable=False)
    cogs: Mapped[float] = mapped_column(Float, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False)
    opex: Mapped[float] = mapped_column(Float, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False)
