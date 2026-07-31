"""Parse financial statement values from Excel (.xlsx) workbooks using pandas."""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

from app.schemas.financial_extraction import FinancialStatementExtraction
from app.services.parsing.extractor import (
    OUTPUT_KEYS,
    FieldRule,
    _match_field_key,
    _parse_amount,
)
from app.services.parsing.parser import FinancialStatementParseError

logger = logging.getLogger(__name__)

# Excel-specific aliases that are common in UK filings but not all covered by
# shared FIELD_RULES (e.g. "Total Turnover", "Administrative Costs").
_EXCEL_FIELD_RULES: list[FieldRule] = [
    FieldRule("revenue", re.compile(r"^\s*total turnover\b", re.IGNORECASE)),
    FieldRule("revenue", re.compile(r"^\s*turnover\b", re.IGNORECASE)),
    FieldRule("revenue", re.compile(r"^\s*sales\b", re.IGNORECASE)),
    FieldRule("cogs", re.compile(r"^\s*cost of sales\b", re.IGNORECASE)),
    FieldRule("gross_profit", re.compile(r"^\s*gross profit\b", re.IGNORECASE)),
    FieldRule("opex", re.compile(r"^\s*administrative costs\b", re.IGNORECASE)),
    # Recognised for logging / future mapping; not stored in the extraction schema.
    FieldRule(
        "operating_profit",
        re.compile(r"^\s*operating profit\b", re.IGNORECASE),
    ),
]

_YEAR_TOKEN_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_PURE_YEAR_RE = re.compile(
    r"^\s*(?:fy|y/?e|year)?\s*((?:19|20)\d{2})\s*(?:£|\$|€|k|'000|000|m)?\s*$",
    re.IGNORECASE,
)


def _match_excel_field_key(label: str) -> str | None:
    """Match a label using Excel-specific rules first, then shared FIELD_RULES."""
    for rule in _EXCEL_FIELD_RULES:
        if rule.pattern.search(label):
            return rule.key
    return _match_field_key(label)


def _cell_as_amount(value: Any) -> float | None:
    """Parse a cell into a float amount, or None if not numeric."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        as_int = int(value)
        # Ignore bare year numbers so period headers are not treated as amounts.
        if as_int == value and 1900 <= as_int <= 2100:
            return None
        return float(value)
    return _parse_amount(str(value))


def _year_from_header(value: Any) -> int | None:
    """Extract a calendar/fiscal year from a column header when present."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        year = int(value)
        if year == value and 1900 <= year <= 2100:
            return year
        return None

    text = str(value).strip()
    if not text:
        return None

    pure = _PURE_YEAR_RE.match(text)
    if pure:
        return int(pure.group(1))

    token = _YEAR_TOKEN_RE.search(text)
    if token:
        return int(token.group(1))

    return None


def _select_latest_period_column(dataframe: pd.DataFrame) -> Any | None:
    """
    Choose the latest period column from columns after the label column.

    Preference order:
    1. Column whose header contains the highest detected year (e.g. 2023 > 2022)
    2. Otherwise the rightmost column that contains at least one numeric value
    """
    if dataframe.shape[1] < 2:
        return None

    period_columns = list(dataframe.columns[1:])
    year_by_column: dict[Any, int] = {}

    for column in period_columns:
        year = _year_from_header(column)
        if year is not None:
            year_by_column[column] = year

    if year_by_column:
        latest_year = max(year_by_column.values())
        for column in period_columns:
            if year_by_column.get(column) == latest_year:
                return column

    # No year headers: use the rightmost numeric period column.
    for column in reversed(period_columns):
        if dataframe[column].map(_cell_as_amount).notna().any():
            return column

    return period_columns[-1] if period_columns else None


def _extract_from_sheet(
    sheet_name: str,
    dataframe: pd.DataFrame,
    results: dict[str, float | None],
) -> list[str]:
    """
    Extract fields from one sheet into ``results``.

    Returns the list of matched label texts for logging.
    """
    matched_labels: list[str] = []

    if dataframe.empty or dataframe.shape[1] == 0:
        logger.info(
            "Excel sheet=%r columns=%s matched_labels=%s",
            sheet_name,
            [],
            matched_labels,
        )
        return matched_labels

    # First column holds financial statement line labels.
    label_column = dataframe.columns[0]
    period_column = _select_latest_period_column(dataframe)

    detected_columns = [str(column) for column in dataframe.columns]
    logger.info(
        "Excel sheet=%r columns=%s selected_period_column=%r",
        sheet_name,
        detected_columns,
        period_column,
    )

    if period_column is None:
        logger.info(
            "Excel sheet=%r columns=%s matched_labels=%s",
            sheet_name,
            detected_columns,
            matched_labels,
        )
        return matched_labels

    for _, row in dataframe.iterrows():
        raw_label = row[label_column]
        if raw_label is None or (isinstance(raw_label, float) and pd.isna(raw_label)):
            continue

        label = str(raw_label).strip()
        if not label:
            continue

        key = _match_excel_field_key(label)
        if key is None:
            continue

        matched_labels.append(label)

        # Skip keys that are recognised but not part of the extraction schema.
        if key not in results:
            continue
        if results[key] is not None:
            continue

        amount = _cell_as_amount(row[period_column])
        if amount is not None:
            results[key] = amount

    logger.info(
        "Excel sheet=%r columns=%s matched_labels=%s",
        sheet_name,
        detected_columns,
        matched_labels,
    )
    return matched_labels


def parse_excel_financial_statement(file_path: str) -> FinancialStatementExtraction:
    """
    Parse a financial statement Excel workbook into ``FinancialStatementExtraction``.

    Uses ``pandas.read_excel`` across all sheets. The first column is treated as
    the label column; values are taken from the latest period/numeric column.

    Args:
        file_path: Path to an ``.xlsx`` workbook.

    Returns:
        Extracted financial fields.

    Raises:
        FinancialStatementParseError: If the workbook cannot be read or no
            supported financial fields are found.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        raise FinancialStatementParseError(
            "file_path must be a non-empty string."
        )

    try:
        sheets = pd.read_excel(file_path, sheet_name=None, header=0)
    except Exception as exc:
        raise FinancialStatementParseError(
            f"Unable to read Excel file: {file_path}"
        ) from exc

    if not sheets:
        raise FinancialStatementParseError(
            f"Excel file has no sheets: {file_path}"
        )

    results: dict[str, float | None] = {key: None for key in OUTPUT_KEYS}

    for sheet_name, dataframe in sheets.items():
        _extract_from_sheet(str(sheet_name), dataframe, results)

    if all(value is None for value in results.values()):
        raise FinancialStatementParseError(
            f"No supported financial fields found in Excel file: {file_path}"
        )

    return FinancialStatementExtraction(**results)
