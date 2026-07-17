import logging

from app.models.schemas import (
    Breach,
    DealRequest,
    DecisionStatus,
    Position,
    RiskEvaluation,
)

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
        self,
        portfolio: list[Position],
        deal: DealRequest,
    ) -> RiskEvaluation:

        current_total_value = self._total_portfolio_value(
            portfolio
        )

        simulated_portfolio = portfolio + [
            Position(
                name=deal.name,
                value=deal.value,
                industry=deal.industry,
            )
        ]

        total_value = self._total_portfolio_value(
            simulated_portfolio
        )

        industry_exposure = self._industry_exposure(
            simulated_portfolio
        )

        capital_utilization_pct = (
            self._capital_utilization_pct(total_value)
        )

        breaches = self._check_limits(
            total_value,
            industry_exposure,
        )

        status = self._decision_status(
            breaches,
            capital_utilization_pct,
            industry_exposure,
        )

        return RiskEvaluation(
            status=status,
            breaches=breaches,
            portfolio_value=total_value,
            capital_utilization_pct=capital_utilization_pct,
            industry_exposure=industry_exposure,
        )


    @staticmethod
    def _total_portfolio_value(
        positions: list[Position],
    ) -> float:
        return sum(
            p.value
            for p in positions
        )


    def _industry_exposure(
        self,
        positions: list[Position],
    ) -> dict[str, float]:

        by_industry: dict[str, float] = {}

        for p in positions:
            by_industry[p.industry] = (
                by_industry.get(p.industry, 0.0)
                + p.value
            )

        return {
            industry: round(
                (value / self.max_portfolio_capital) * 100,
                4,
            )
            for industry, value in sorted(
                by_industry.items()
            )
        }


    def _capital_utilization_pct(
        self,
        total_portfolio_value: float,
    ) -> float:

        return round(
            (total_portfolio_value / self.max_portfolio_capital)
            * 100,
            4,
        )


    def _check_limits(
        self,
        total_portfolio_value: float,
        industry_exposure: dict[str, float],
    ) -> list[Breach]:

        breaches: list[Breach] = []

        if total_portfolio_value > self.max_portfolio_capital:
            breaches.append(
                Breach(
                    rule="portfolio_capital_limit",
                    limit_pct=self.max_portfolio_capital,
                    actual_pct=total_portfolio_value,
                    detail=(
                        f"Portfolio value {total_portfolio_value:,.2f} "
                        f"exceeds max capital "
                        f"{self.max_portfolio_capital:,.2f}."
                    ),
                )
            )


        for industry, pct in industry_exposure.items():

            if pct > (
                self.industry_limit_pct
                + self.industry_limit_epsilon
            ):
                breaches.append(
                    Breach(
                        rule="industry_concentration_limit",
                        limit_pct=self.industry_limit_pct,
                        actual_pct=pct,
                        detail=(
                            f"Industry '{industry}' exposure "
                            f"{pct}% exceeds limit "
                            f"{self.industry_limit_pct}%"
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

        if self._near_limits(
            capital_utilization_pct,
            industry_exposure,
        ):
            return DecisionStatus.WARNING

        return DecisionStatus.APPROVED


    def _near_limits(
        self,
        capital_utilization_pct: float,
        industry_exposure: dict[str, float],
    ) -> bool:

        return (
            capital_utilization_pct >= 80
            or any(
                pct >= self.industry_limit_pct * 0.8
                for pct in industry_exposure.values()
            )
        )