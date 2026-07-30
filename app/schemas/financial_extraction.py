from pydantic import BaseModel


class FinancialStatementExtraction(BaseModel):
    revenue: float | None = None
    cogs: float | None = None
    gross_profit: float | None = None
    opex: float | None = None
    cash: float | None = None
    assets: float | None = None
    liabilities: float | None = None
    equity: float | None = None
