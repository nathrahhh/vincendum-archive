from app.models.schemas import (
    Breach,
    DealRequest,
    DecisionStatus,
    Position,
    RiskEvaluation,
)

INDUSTRY_LIMIT_PCT = 20.0
SINGLE_POSITION_LIMIT_PCT = 10.0


class RiskEngine:
    """Pre-trade concentration and exposure checks for private lending portfolios."""

    def __init__(
        self,
        industry_limit_pct: float = INDUSTRY_LIMIT_PCT,
        single_position_limit_pct: float = SINGLE_POSITION_LIMIT_PCT,
    ) -> None:
        self.industry_limit_pct = industry_limit_pct
        self.single_position_limit_pct = single_position_limit_pct

    def evaluate_deal(
        self, portfolio: list[Position], deal: DealRequest
    ) -> RiskEvaluation:
        simulated = portfolio + [
            Position(name=deal.name, value=deal.value, industry=deal.industry)
        ]
        total_value = self._total_portfolio_value(simulated)
        industry_exposure = self._industry_exposure(simulated, total_value)
        position_exposure = self._position_exposure(simulated, total_value)
        breaches = self._check_limits(industry_exposure, position_exposure)
        status = self._decision_status(
            breaches, industry_exposure, position_exposure
        )

        return RiskEvaluation(
            status=status,
            breaches=breaches,
            portfolio_value=total_value,
            industry_exposure=industry_exposure,
            position_exposure=position_exposure,
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

    @staticmethod
    def _position_exposure(
        positions: list[Position], total_value: float
    ) -> dict[str, float]:
        if total_value <= 0:
            return {}
        return {
            p.name: round((p.value / total_value) * 100, 4)
            for p in sorted(positions, key=lambda x: x.name)
        }

    def _check_limits(
        self,
        industry_exposure: dict[str, float],
        position_exposure: dict[str, float],
    ) -> list[Breach]:
        breaches: list[Breach] = []

        for industry, pct in industry_exposure.items():
            if pct > self.industry_limit_pct:
                breaches.append(
                    Breach(
                        rule="industry_limit",
                        limit_pct=self.industry_limit_pct,
                        actual_pct=pct,
                        detail=(
                            f"Industry '{industry}' exposure {pct}% "
                            f"exceeds limit {self.industry_limit_pct}%"
                        ),
                    )
                )

        for name, pct in position_exposure.items():
            if pct > self.single_position_limit_pct:
                breaches.append(
                    Breach(
                        rule="single_position_limit",
                        limit_pct=self.single_position_limit_pct,
                        actual_pct=pct,
                        detail=(
                            f"Position '{name}' exposure {pct}% "
                            f"exceeds limit {self.single_position_limit_pct}%"
                        ),
                    )
                )

        return breaches

    def _decision_status(
        self,
        breaches: list[Breach],
        industry_exposure: dict[str, float],
        position_exposure: dict[str, float],
    ) -> DecisionStatus:
        if breaches:
            return DecisionStatus.REJECTED
        if self._near_limits(industry_exposure, position_exposure):
            return DecisionStatus.WARNING
        return DecisionStatus.APPROVED

    def _near_limits(
        self,
        industry_exposure: dict[str, float],
        position_exposure: dict[str, float],
    ) -> bool:
        """Warn when exposure is at or above 80% of a concentration limit."""
        industry_warn = self.industry_limit_pct * 0.8
        position_warn = self.single_position_limit_pct * 0.8
        return any(pct >= industry_warn for pct in industry_exposure.values()) or any(
            pct >= position_warn for pct in position_exposure.values()
        )
