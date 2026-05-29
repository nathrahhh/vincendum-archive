import re

from app.models.breach import BreachORM
from app.models.schemas import Breach

UNKNOWN_INDUSTRY = "Unknown"
PORTFOLIO_INDUSTRY = "Portfolio"


def industry_from_breach_detail(detail: str) -> str | None:
    match = re.search(r"Industry '([^']+)' exposure", detail)
    return match.group(1) if match else None


def resolve_breach_industry(breach: BreachORM) -> str:
    if breach.industry:
        return breach.industry
    if breach.rule == "portfolio_capital_limit":
        return PORTFOLIO_INDUSTRY
    from_detail = industry_from_breach_detail(breach.detail)
    if from_detail:
        return from_detail
    return UNKNOWN_INDUSTRY


def resolve_breach_reason(breach: BreachORM) -> str:
    if breach.reason:
        return breach.reason
    if breach.rule == "industry_concentration_limit":
        return "Industry concentration risk exceeded limit"
    if breach.rule == "portfolio_capital_limit":
        return "Portfolio capital usage exceeded limit"
    return breach.detail


def reason_for_new_breach(breach: Breach) -> str:
    if breach.rule == "industry_concentration_limit":
        return "Industry concentration risk exceeded limit"
    if breach.rule == "portfolio_capital_limit":
        return "Portfolio capital usage exceeded limit"
    return breach.detail


def industry_for_new_breach(breach: Breach, deal_industry: str) -> str:
    if breach.rule == "portfolio_capital_limit":
        return PORTFOLIO_INDUSTRY
    return deal_industry
