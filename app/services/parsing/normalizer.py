"""Map accounting terminology to standardized field names."""

from __future__ import annotations

# Canonical field name → accepted label aliases.
# Add new aliases (or new canonical keys) here to extend support.
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
    "opex": (
        "opex",
        "operating expenses",
        "administrative expenses",
        "selling expenses",
    ),
    "gross_profit": (
        "gross profit",
        "gross income",
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


def _build_label_map(groups: dict[str, tuple[str, ...]]) -> dict[str, str]:
    """Flatten alias groups into a lookup of normalized alias → canonical key."""
    mapping: dict[str, str] = {}
    for canonical, aliases in groups.items():
        for alias in aliases:
            mapping[_canonicalize_text(alias)] = canonical
    return mapping


def _canonicalize_text(value: str) -> str:
    """Lowercase and collapse whitespace for stable label matching."""
    return " ".join(value.lower().strip().split())


# Flat lookup used by normalize_label. Rebuilds whenever _LABEL_GROUPS changes.
LABEL_MAP: dict[str, str] = _build_label_map(_LABEL_GROUPS)


def normalize_label(label: str) -> str | None:
    """
    Convert an accounting label into a standardized field name.

    Args:
        label: Raw line-item label from a financial statement
            (e.g. ``"Net Sales"``, ``"COGS"``).

    Returns:
        Canonical field name such as ``"revenue"`` or ``"cogs"``,
        or ``None`` if the label is not recognized.
    """
    if not label or not label.strip():
        return None

    return LABEL_MAP.get(_canonicalize_text(label))


def normalize_financial_data(raw_data: dict) -> dict:
    """
    Convert extracted accounting labels into standardized field names.

    Args:
        raw_data: Dictionary of raw label → value pairs from extraction.

    Returns:
        Dictionary keyed by canonical field names. Unknown labels are omitted.
    """
    # TODO: Parse numeric strings (commas, currency symbols, parentheses)
    # when values are still raw strings rather than floats.
    normalized: dict = {}

    for label, value in raw_data.items():
        key = normalize_label(str(label))
        if key is None:
            continue
        # First match wins when multiple aliases map to the same key.
        if key not in normalized:
            normalized[key] = value

    return normalized
