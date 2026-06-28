import logging

from app.models.schemas import Breach, DealRequest, DecisionStatus, Position, RiskEvaluation

MAX_PORTFOLIO_CAPITAL = 10_000_000.0
INDUSTRY_LIMIT_PCT = 20.0
INDUSTRY_LIMIT_EPSILON = 0.01

logger = logging.getLogger(__name__)


class RiskEngine:
    """Pre-trade risk checks for private lending portfolios."""

    def __init__(
        self,
        max_portfolio_capital: float = MAX_PORTFOLIO_CAPITAL,
        industry_limit_pct: float = INDUSTRY_LIMIT_PCT,
        industry_limit_epsilon: float = INDUSTRY_LIMIT_EPSILON,
    ) -> None:
        self.max_portfolio_capital = max_portfolio_capital
        self.industry_limit_pct = industry_limit_pct
        self.industry_limit_epsilon = industry_limit_epsilon

    def evaluate_deal(
        self, portfolio: list[Position], deal: DealRequest
    ) -> RiskEvaluation:
        current_total_value = self._total_portfolio_value(portfolio)
        simulated_portfolio = portfolio + [Position(name=deal.name, value=deal.value, industry=deal.industry)]
        total_value = self._total_portfolio_value(simulated_portfolio)
        industry_exposure = self._industry_exposure(simulated_portfolio)
        logger.info(
            "risk_evaluation_inputs current_total_value=%.4f simulated_total_value=%.4f deal_name=%s deal_value=%.4f deal_industry=%s industry_exposure=%s",
            current_total_value,
            total_value,
            deal.name,
            deal.value,
            deal.industry,
            industry_exposure,
        )
        capital_utilization_pct = self._capital_utilization_pct(total_value)
        breaches = self._check_limits(total_value, industry_exposure)
        status = self._decision_status(
            breaches=breaches,
            capital_utilization_pct=capital_utilization_pct,
            industry_exposure=industry_exposure,
        )
        breach_reasons = self.get_breach_reasons(breaches)
        logger.info(
            "risk_evaluation_decision status=%s breach_reasons=%s capital_utilization_pct=%.4f",
            status.value,
            breach_reasons,
            capital_utilization_pct,
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

    def _industry_exposure(self, positions: list[Position]) -> dict[str, float]:
        if self.max_portfolio_capital <= 0:
            return {}
        by_industry: dict[str, float] = {}
        for p in positions:
            by_industry[p.industry] = by_industry.get(p.industry, 0.0) + p.value
        return {
            industry: round((value / self.max_portfolio_capital) * 100, 4)
            for industry, value in sorted(by_industry.items())
        }

    
    def _capital_utilization_pct(self, total_portfolio_value: float) -> float:
        if self.max_portfolio_capital <= 0:
            return 0.0
        return round((total_portfolio_value / self.max_portfolio_capital) * 100, 4)

    def _check_limits(self, total_portfolio_value: float, industry_exposure: dict[str, float]) -> list[Breach]:
        breaches: list[Breach] = []

        if total_portfolio_value > self.max_portfolio_capital:
            logger.info(
                "breach_triggered type=capital total_portfolio_value=%.4f max_portfolio_capital=%.4f",
                total_portfolio_value,
                self.max_portfolio_capital,
            )
            breaches.append(
                Breach(
                    rule="portfolio_capital_limit",
                    limit_pct=self.max_portfolio_capital,
                    actual_pct=total_portfolio_value,
                    detail=(
                        f"Portfolio value {total_portfolio_value:,.2f} exceeds "
                        f"max capital {self.max_portfolio_capital:,.2f}."
                    ),
                )
            )

        logger.debug("Industry exposures calculated: %s", industry_exposure)
        for industry, pct in industry_exposure.items():
            # Use epsilon to avoid false breaches from floating point noise
            if pct > (self.industry_limit_pct + self.industry_limit_epsilon):
                logger.info(
                    "breach_triggered type=industry industry=%s pct=%.6f limit=%.6f epsilon=%.6f",
                    industry,
                    pct,
                    self.industry_limit_pct,
                    self.industry_limit_epsilon,
                )
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

    def get_breach_reasons(self, breaches: list[Breach]) -> list[str]:
        reasons: list[str] = []
        for breach in breaches:
            if breach.rule == "portfolio_capital_limit":
                reasons.append("CAPITAL_OVER_LIMIT")
                continue
            if breach.rule == "industry_concentration_limit":
                industry_name = self._extract_industry_from_detail(breach.detail)
                reasons.append(f"{industry_name.upper()}_OVER_20%")
                continue
            reasons.append(breach.rule.upper())
        return reasons

    @staticmethod
    def _extract_industry_from_detail(detail: str) -> str:
        marker_start = "Industry '"
        marker_end = "' exposure"
        start = detail.find(marker_start)
        end = detail.find(marker_end)
        if start == -1 or end == -1 or end <= start + len(marker_start):
            return "INDUSTRY"
        return detail[start + len(marker_start):end]
