from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
    """Client-submitted deal application fields.

    The client requests the deal name, amount, and desired term.
    Lender-controlled repayment terms such as interest rate and
    repayment dates are set during approval.
    """

    name: str = Field(..., min_length=1)
    value: float = Field(..., gt=0)
    term_months: int = Field(..., gt=0)


class DealApprovalRequest(BaseModel):
    """Lender-confirmed repayment terms for approving a pending deal."""

    principal_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0)
    interest_rate_type: str = Field(..., min_length=1)
    repayment_method: str = Field(..., min_length=1)
    term_months: int = Field(..., gt=0)
    start_date: date
    payment_frequency: str = Field(..., min_length=1)
    first_payment_date: date
    maturity_date: date | None = None


class DealRecord(BaseModel):
    id: int
    client_id: int
    name: str
    value: float
    status: str | None = None
    principal_amount: float | None = None
    interest_rate: float | None = None
    interest_rate_type: str | None = None
    repayment_method: str | None = None
    term_months: int | None = None
    start_date: date | None = None
    maturity_date: date | None = None
    payment_frequency: str | None = None
    first_payment_date: date | None = None

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
    status: str | None = None


class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    storage_type: str = Field(default="s3", min_length=1)
    storage_key: str | None = None
    external_url: str | None = None


class DocumentRecord(BaseModel):
    id: int
    lender_id: int
    client_id: int | None
    application_id: int | None
    name: str
    storage_type: str
    storage_key: str | None
    external_url: str | None
    created_at: datetime


class ClientFinancialResponse(BaseModel):
    client_id: int
    historical: list[ClientFinancialRecord]


class AuditLogRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lender_id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: int
    created_at: datetime
    changes: dict[str, Any] | None = None
    # ORM attribute is `metadata_` (DB column name is `metadata`).
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_",
    )


class ClientApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    credit_limit: float = Field(..., gt=0)
    registered_business_name: str | None = None
    companies_house_number: str | None = None
    incorporation_year: int | None = None
    headcount: int | None = None
    revenue_last_fy: float | None = None


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
    slug: str


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    role: str
    lender_id: int | None
    client_id: int | None


class ForecastRevenuePoint(BaseModel):
    month: str
    revenue: float


StatisticalForecastModelName = Literal[
    "naive",
    "seasonal_naive",
    "ets",
    "holt_winters",
    "prophet",
]


class StatisticalForecastResponse(BaseModel):
    """Shared revenue-only response for all statistical forecasting models."""

    client_id: int
    model: StatisticalForecastModelName
    historical: list[ForecastRevenuePoint]
    forecast: list[ForecastRevenuePoint]
    unavailable_reason: str | None = None


class ForecastBacktestModelResult(BaseModel):
    model: StatisticalForecastModelName
    mae: float | None = None
    available: bool
    unavailable_reason: str | None = None


class ForecastBacktestResponse(BaseModel):
    """Historical MAE comparison across statistical revenue forecasting models."""

    client_id: int
    metric: Literal["mae"] = "mae"
    holdout_months: int
    best_model: StatisticalForecastModelName | None = None
    results: list[ForecastBacktestModelResult]
