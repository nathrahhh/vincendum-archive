"""Parse financial statement values from CSV files."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.schemas.financial_extraction import FinancialStatementExtraction
from app.services.parsing.parser import FinancialStatementParseError

SUPPORTED_FIELDS: tuple[str, ...] = (
    "revenue",
    "cogs",
    "gross_profit",
    "opex",
    "cash",
    "assets",
    "liabilities",
    "equity",
)


def _parse_numeric(value: Any) -> float | None:
    """Convert a cell value to float, or None if it cannot be parsed."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    token = str(value).strip()
    if not token:
        return None

    negative = token.startswith("(") and token.endswith(")")
    if negative:
        token = token[1:-1]

    token = token.replace("$", "").replace(",", "").strip()
    if not token:
        return None

    try:
        parsed = float(token)
    except ValueError:
        return None

    return -abs(parsed) if negative else parsed


def _first_numeric_in_column(series: pd.Series) -> float | None:
    """Return the first parseable numeric value in a column."""
    for value in series.tolist():
        parsed = _parse_numeric(value)
        if parsed is not None:
            return parsed
    return None


def parse_csv_financial_statement(file_path: str) -> FinancialStatementExtraction:
    """
    Parse a financial statement CSV into a ``FinancialStatementExtraction``.

    Expects a wide CSV where supported field names appear as column headers.
    Column matching is case-insensitive. Missing columns remain ``None``.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Extracted financial fields with ``None`` for any missing values.

    Raises:
        FinancialStatementParseError: If the file cannot be read, the CSV is
            empty, or no supported financial fields are found.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        raise FinancialStatementParseError(
            "file_path must be a non-empty string."
        )

    try:
        dataframe = pd.read_csv(file_path)
    except Exception as exc:
        raise FinancialStatementParseError(
            f"Unable to read CSV file: {file_path}"
        ) from exc

    if dataframe.empty:
        raise FinancialStatementParseError(
            f"CSV file is empty: {file_path}"
        )

    columns_by_lower = {
        str(column).strip().lower(): column for column in dataframe.columns
    }

    extracted: dict[str, float | None] = {}
    for field in SUPPORTED_FIELDS:
        source_column = columns_by_lower.get(field)
        if source_column is None:
            extracted[field] = None
            continue
        extracted[field] = _first_numeric_in_column(dataframe[source_column])

    if all(value is None for value in extracted.values()):
        raise FinancialStatementParseError(
            f"No supported financial fields found in CSV: {file_path}"
        )

    return FinancialStatementExtraction(**extracted)
