"""Descriptive metadata helpers for breach records.

Constructs reason and industry labels for supported breach rules.
Does not access the database or create/update BreachORM rows.
"""

from __future__ import annotations

PORTFOLIO_CAPITAL_LIMIT = "portfolio_capital_limit"
INDUSTRY_CONCENTRATION_LIMIT = "industry_concentration_limit"

PORTFOLIO_INDUSTRY = "Portfolio"

_REASONS: dict[str, str] = {
    PORTFOLIO_CAPITAL_LIMIT: "Portfolio capital usage exceeded limit",
    INDUSTRY_CONCENTRATION_LIMIT: "Industry concentration risk exceeded limit",
}


def reason_for_rule(rule: str, detail: str) -> str:
    """
    Return the canonical reason for a supported breach rule.

    Falls back to ``detail`` for unrecognized rules so callers still have
    explanatory text without inventing structured business data.
    """
    return _REASONS.get(rule, detail)


def industry_for_rule(rule: str, industry: str | None = None) -> str | None:
    """
    Return the industry label for a breach rule.

    Portfolio capital breaches are labeled ``Portfolio``.
    Industry concentration breaches use the caller-provided industry.
    """
    if rule == PORTFOLIO_CAPITAL_LIMIT:
        return PORTFOLIO_INDUSTRY
    if rule == INDUSTRY_CONCENTRATION_LIMIT:
        return industry
    return industry
