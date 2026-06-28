from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


class Position(BaseModel):
    name: str = Field(..., min_length=1)
    value: float = Field(..., gt=0)
    industry: str = Field(..., min_length=1)


class IndustryExposure(BaseModel):
    industry: str
    value: float
    percentage: float


class PortfolioResponse(BaseModel):
    positions: list[Position]
    total_portfolio_value: float
    capital_utilization_pct: float
    industry_exposure: list[IndustryExposure]


class DealRequest(BaseModel):
    name: str = Field(..., min_length=1)
    value: float = Field(..., gt=0)
    industry: str = Field(..., min_length=1)


class DealRecord(BaseModel):
    id: int
    name: str
    value: float
    industry: str
    status: str | None = None


class Breach(BaseModel):
    rule: Literal["industry_concentration_limit", "portfolio_capital_limit"]
    limit_pct: float
    actual_pct: float
    detail: str


class RiskEvaluation(BaseModel):
    status: DecisionStatus
    breaches: list[Breach]
    portfolio_value: float
    capital_utilization_pct: float
    industry_exposure: dict[str, float]


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "Credit Risk + Concentration Risk Engine"


class ClientFinancialCreate(BaseModel):
    client_id: int
    month: date
    revenue: float
    cogs: float
    opex: float
    cash_balance: float


class ClientApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    credit_limit: float = Field(..., gt=0)
