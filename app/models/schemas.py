from datetime import date
from enum import Enum
from typing import Literal
from typing import Annotated, Literal

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

class ForecastAssumptions(BaseModel):
    revenue_growth_rate: float
    average_cogs_ratio: float
    average_opex_ratio: float
    average_gross_margin: float | None


class ForecastHistoricalRecord(BaseModel):
    month: str
    revenue: float
    cogs: float
    opex: float
    reported_gross_profit: float | None
    calculated_gross_profit: float
    cash_balance: float

class DeterministicForecastRecord(BaseModel):
    month: str
    revenue: float
    cogs: float
    opex: float
    gross_profit_margin_method: float | None
    gross_profit_cogs_method: float
    gross_profit_difference: float | None
    net_cash_flow: float
    cash_balance: float

class GrossProfitAlert(BaseModel):
    month: str
    message: str
    difference_pct: float


class DeterministicForecastAlerts(BaseModel):
    gross_profit_alerts: list[GrossProfitAlert]

class DeterministicForecast(BaseModel):
    client_id: int
    model_type: Literal["deterministic"]

    assumptions: ForecastAssumptions
    historical: list[ForecastHistoricalRecord]
    forecast: list[DeterministicForecastRecord]
    alerts: DeterministicForecastAlerts

class ProphetHistoricalRecord(BaseModel):
    month: str
    revenue: float
    gross_profit: float

class ProphetForecastRecord(BaseModel):
    month: str
    revenue: float

    base: float
    best: float
    worst: float

    lower_bound: float
    upper_bound: float

class ProphetForecast(BaseModel):
    client_id: int
    model_type: Literal["prophet"]

    historical: list[ProphetHistoricalRecord]
    forecast: list[ProphetForecastRecord]

ClientForecast = Annotated[
    ProphetForecast | DeterministicForecast,
    Field(discriminator="model_type"),
]
