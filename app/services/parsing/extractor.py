"""Extract financial statement line items from raw text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FieldRule:
    """Maps a line-item label pattern to a canonical output key."""

    key: str
    pattern: re.Pattern[str]


# Add new FieldRule entries here to support additional statement labels.
FIELD_RULES: list[FieldRule] = [
    FieldRule("revenue", re.compile(r"^\s*revenue\b", re.IGNORECASE)),
    FieldRule("revenue", re.compile(r"^\s*net sales\b", re.IGNORECASE)),
    FieldRule("revenue", re.compile(r"^\s*sales\b", re.IGNORECASE)),

    FieldRule("cogs", re.compile(r"^\s*cost of goods sold\b", re.IGNORECASE)),
    FieldRule("cogs", re.compile(r"^\s*cost of sales\b", re.IGNORECASE)),
    FieldRule("cogs", re.compile(r"^\s*cost of revenue\b", re.IGNORECASE)),
    FieldRule("cogs", re.compile(r"^\s*cogs\b", re.IGNORECASE)),

    FieldRule("gross_profit", re.compile(r"^\s*gross profit\b", re.IGNORECASE)),
    FieldRule("gross_profit", re.compile(r"^\s*gross income\b", re.IGNORECASE)),

    FieldRule("opex", re.compile(r"^\s*operating expenses\b", re.IGNORECASE)),
    FieldRule("cash", re.compile(r"^\s*cash\b(?!\s+flow)", re.IGNORECASE)),
    FieldRule("assets", re.compile(r"^\s*total assets\b", re.IGNORECASE)),
    FieldRule(
        "liabilities",
        re.compile(r"^\s*total liabilities\b", re.IGNORECASE),
    ),
    FieldRule("equity", re.compile(r"^\s*equity\b", re.IGNORECASE)),
]


OUTPUT_KEYS: tuple[str, ...] = (
    "revenue",
    "cogs",
    "gross_profit",
    "opex",
    "cash",
    "assets",
    "liabilities",
    "equity",
)


# Captures amounts such as 1,250,000 / $1,250.50 / (12,000)
_AMOUNT_RE = re.compile(
    r"\(?\$?-?[\d,]+(?:\.\d+)?\)?",
)


def _parse_amount(raw: str) -> float | None:
    """Parse a numeric string, stripping commas and handling parentheses."""
    token = raw.strip()

    if not token:
        return None

    negative = token.startswith("(") and token.endswith(")")

    if negative:
        token = token[1:-1]

    token = token.replace("$", "").replace(",", "").strip()

    if not token:
        return None

    try:
        value = float(token)
    except ValueError:
        return None

    return -abs(value) if negative else value


def _extract_amount_from_line(line: str) -> float | None:
    """Return the last parseable amount found on a line, if any."""
    matches = _AMOUNT_RE.findall(line)

    if not matches:
        return None

    for candidate in reversed(matches):
        value = _parse_amount(candidate)

        if value is not None:
            return value

    return None


def _match_field_key(line: str) -> str | None:
    """Return the canonical key for the first matching field rule on a line."""
    for rule in FIELD_RULES:
        if rule.pattern.search(line):
            return rule.key

    return None


def extract_financial_data(text: str) -> dict[str, float | None]:
    """
    Scan statement text line by line and extract known financial fields.

    Returns:
        Dictionary containing revenue, cogs, gross_profit, opex,
        cash, assets, liabilities, and equity.
        Missing values are None.
    """

    results: dict[str, float | None] = {
        key: None for key in OUTPUT_KEYS
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        key = _match_field_key(line)

        if key is None or results[key] is not None:
            continue

        amount = _extract_amount_from_line(line)

        if amount is not None:
            results[key] = amount

    return results