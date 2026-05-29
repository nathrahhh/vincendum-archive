from app.models.schemas import IndustryExposure, PortfolioResponse, Position

MAX_PORTFOLIO_CAPITAL = 10_000_000.0


def _normalize_industry_percentages(exposure: list[IndustryExposure]) -> None:
    """Adjust rounded percentages so they sum to exactly 100%."""
    if not exposure:
        return
    rounded_sum = sum(item.percentage for item in exposure)
    drift = round(100.0 - rounded_sum, 4)
    if drift == 0:
        return
    largest = max(exposure, key=lambda item: item.value)
    largest.percentage = round(largest.percentage + drift, 4)


def build_portfolio_response(positions: list[Position]) -> PortfolioResponse:
    total_portfolio_value = sum(position.value for position in positions)

    if total_portfolio_value <= 0:
        return PortfolioResponse(
            positions=positions,
            total_portfolio_value=0.0,
            capital_utilization_pct=0.0,
            industry_exposure=[],
        )

    capital_utilization_pct = round(
        (total_portfolio_value / MAX_PORTFOLIO_CAPITAL) * 100, 4
    )

    by_industry: dict[str, float] = {}
    for position in positions:
        by_industry[position.industry] = by_industry.get(position.industry, 0.0) + position.value

    industry_exposure = [
        IndustryExposure(
            industry=industry,
            value=value,
            percentage=round((value / total_portfolio_value) * 100, 4),
        )
        for industry, value in sorted(by_industry.items())
    ]
    _normalize_industry_percentages(industry_exposure)

    return PortfolioResponse(
        positions=positions,
        total_portfolio_value=total_portfolio_value,
        capital_utilization_pct=capital_utilization_pct,
        industry_exposure=industry_exposure,
    )
