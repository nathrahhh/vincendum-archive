"""Map accounting terminology to standardized field names."""

from __future__ import annotations


# Canonical field name → accepted accounting labels.
_LABEL_GROUPS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "revenue",
        "sales",
        "net sales",
        "turnover",
    ),
    "cogs": (
        "cogs",
        "cost of goods sold",
        "cost of sales",
        "cost of revenue",
    ),
    "gross_profit": (
        "gross profit",
        "gross income",
    ),
    "opex": (
        "opex",
        "operating expenses",
        "administrative expenses",
        "selling expenses",
    ),
    "cash": (
        "cash",
        "cash and cash equivalents",
    ),
    "assets": (
        "assets",
        "total assets",
    ),
    "liabilities": (
        "liabilities",
        "total liabilities",
    ),
    "equity": (
        "equity",
        "total equity",
        "shareholders equity",
        "stockholders equity",
    ),
}


def _canonicalize_text(value: str) -> str:
    """Normalize text for matching."""
    return " ".join(value.lower().strip().split())


def _build_label_map(
    groups: dict[str, tuple[str, ...]]
) -> dict[str, str]:
    """
    Build lookup:
    
    "gross profit" -> "gross_profit"
    "revenue" -> "revenue"
    """
    mapping: dict[str, str] = {}

    for canonical, aliases in groups.items():
        for alias in aliases:
            mapping[_canonicalize_text(alias)] = canonical

    return mapping


LABEL_MAP = _build_label_map(_LABEL_GROUPS)


def normalize_label(label: str) -> str | None:
    """
    Convert accounting labels into application field names.
    """

    if not label or not label.strip():
        return None

    cleaned = _canonicalize_text(label)

    # Already standardized?
    if cleaned in _LABEL_GROUPS:
        return cleaned

    return LABEL_MAP.get(cleaned)


def normalize_financial_data(raw_data: dict) -> dict:
    """
    Convert extracted financial data into standardized fields.

    Accepts both:

    {
        "Gross Profit": 400000
    }

    and:

    {
        "gross_profit": 400000
    }
    """

    normalized: dict = {}

    for label, value in raw_data.items():
        key = normalize_label(str(label))

        if key is None:
            continue

        if key not in normalized:
            normalized[key] = value

    return normalized