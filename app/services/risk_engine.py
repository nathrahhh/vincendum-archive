from app.models.schemas import Breach, DealRequest, DecisionStatus, Position, RiskEvaluation

MAX_PORTFOLIO_CAPITAL = 10_000_000.0
INDUSTRY_LIMIT_PCT = 20.0


class RiskEngine:
    """Pre-trade risk checks for private lending portfolios."""

    def __init__(
        self,
        max_portfolio_capital: float = MAX_PORTFOLIO_CAPITAL,
        industry_limit_pct: float = INDUSTRY_LIMIT_PCT,
    ) -> None:
        self.max_portfolio_capital = max_portfolio_capital
        self.industry_limit_pct = industry_limit_pct

    def evaluate_deal(
        self, portfolio: list[Position], deal: DealRequest
    ) -> RiskEvaluation:
        simulated_portfolio = portfolio + [Position(name=deal.name, value=deal.value, industry=deal.industry)]
        total_value = self._total_portfolio_value(simulated_portfolio)
        industry_exposure = self._industry_exposure(simulated_portfolio, total_value)
        capital_utilization_pct = self._capital_utilization_pct(total_value)
        breaches = self._check_limits(capital_utilization_pct, industry_exposure)
        status = self._decision_status(
            breaches=breaches,
            capital_utilization_pct=capital_utilization_pct,
            industry_exposure=industry_exposure,
        )

        return RiskEvaluation(
            status=status,
            breaches=breaches,
            portfolio_value=total_value,
            capital_utilization_pct=capital_utilization_pct,
            industry_exposure=industry_exposure,
        )

    @staticmethod
    def _total_portfolio_value(positions: list[Position]) -> float:
        return sum(p.value for p in positions)

    @staticmethod
    def _industry_exposure(
        positions: list[Position], total_value: float
    ) -> dict[str, float]:
        if total_value <= 0:
            return {}
        by_industry: dict[str, float] = {}
        for p in positions:
            by_industry[p.industry] = by_industry.get(p.industry, 0.0) + p.value
        return {
            industry: round((value / total_value) * 100, 4)
            for industry, value in sorted(by_industry.items())
        }

    
    def _capital_utilization_pct(self, total_portfolio_value: float) -> float:
        if self.max_portfolio_capital <= 0:
            return 0.0
        return round((total_portfolio_value / self.max_portfolio_capital) * 100, 4)

    def _check_limits(self, capital_utilization_pct: float, industry_exposure: dict[str, float]) -> list[Breach]:
        breaches: list[Breach] = []

        if capital_utilization_pct > 100:
            breaches.append(
                Breach(
                    rule="portfolio_capital_limit",
                    limit_pct=100.0,
                    actual_pct=capital_utilization_pct,
                    detail=(
                        f"Portfolio deployed capital {capital_utilization_pct}% exceeds "
                        f"the 100% capital limit ({self.max_portfolio_capital:,.0f})."
                    ),
                )
            )

        for industry, pct in industry_exposure.items():
            if pct > round(self.industry_limit_pct, 4):
                breaches.append(
                    Breach(
                        rule="industry_concentration_limit",
                        limit_pct=self.industry_limit_pct,
                        actual_pct=pct,
                        detail=(
                            f"Industry '{industry}' exposure {pct}% "
                            f"exceeds limit {self.industry_limit_pct}%"
                        ),
                    )
                )

        return breaches

    def _decision_status(
        self,
        breaches: list[Breach],
        capital_utilization_pct: float,
        industry_exposure: dict[str, float],
    ) -> DecisionStatus:
        if breaches:
            return DecisionStatus.REJECTED
        if self._near_limits(capital_utilization_pct, industry_exposure):
            return DecisionStatus.WARNING
        return DecisionStatus.APPROVED

    def _near_limits(
        self,
        capital_utilization_pct: float,
        industry_exposure: dict[str, float],
    ) -> bool:
        """Warn when utilization is at or above 80% of a hard limit."""
        industry_warn = self.industry_limit_pct * 0.8
        capital_warn = 80.0
        return capital_utilization_pct >= capital_warn or any(
            pct >= industry_warn for pct in industry_exposure.values()
        )
