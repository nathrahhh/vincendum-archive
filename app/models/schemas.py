from datetime import date, datetime
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
    client_id: int
    name: str = Field(..., min_length=1)
    value: float = Field(..., gt=0)
    industry: str = Field(..., min_length=1)


class DealRecord(BaseModel):
    id: int
    client_id: int | None = None
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
    gross_profit: float
    opex: float
    cash_balance: float


class ClientFinancialRecord(BaseModel):
    id: int
    client_id: int
    month: date
    revenue: float
    cogs: float
    gross_profit: float
    opex: float
    cash_balance: float


class ClientFinancialResponse(BaseModel):
    client_id: int
    historical: list[ClientFinancialRecord]

class ClientApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    credit_limit: float = Field(..., gt=0)


class ClientCreditLimitUpdate(BaseModel):
    credit_limit: float = Field(..., gt=0)


class ClientInviteRequest(BaseModel):
    email: str = Field(..., min_length=3)


class ClientInviteResponse(BaseModel):
    id: int
    client_id: int
    email: str
    status: str
    expires_at: datetime
    # Returned once for development/testing; never store or log long-term.
    token: str
    invitation_url: str


class ClientInvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ClientInvitationAcceptResponse(BaseModel):
    invitation_id: int
    client_id: int
    client_name: str
    status: str
    role: str


class LenderOnboardRequest(BaseModel):
    name: str = Field(..., min_length=1)


class LenderResponse(BaseModel):
    id: int
    name: str


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    role: str
    lender_id: int | None
    client_id: int | None


class ForecastRevenuePoint(BaseModel):
    month: str
    revenue: float


class DeterministicForecastPoint(BaseModel):
    month: str
    revenue: float
    cogs: float
    opex: float
    reported_gross_profit: float | None = None
    calculated_gross_profit: float | None = None
    cash_balance: float
    gross_profit_margin_method: float | None = None
    gross_profit_cogs_method: float
    gross_profit_difference: float | None = None
    net_cash_flow: float


class ProphetForecastPoint(BaseModel):
    month: str
    revenue: float
    lower_bound: float
    upper_bound: float


class ProphetForecastResponse(BaseModel):
    client_id: int
    model: Literal["prophet"]
    historical: list[ForecastRevenuePoint]
    forecast: list[ProphetForecastPoint]


class DeterministicForecastResponse(BaseModel):
    client_id: int
    model: Literal["deterministic"] = "deterministic"
    assumptions: dict
    historical: list[dict]
    forecast: list[DeterministicForecastPoint]
    alerts: dict
