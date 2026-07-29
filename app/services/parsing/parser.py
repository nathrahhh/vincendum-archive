"""Orchestrate PDF financial statement parsing end-to-end."""

from __future__ import annotations

from app.services.parsing.extractor import extract_financial_data
from app.services.parsing.normalizer import normalize_financial_data
from app.services.parsing.pdf_reader import PDFReadError, extract_text_from_pdf


class FinancialStatementParseError(Exception):
    """Raised when the financial statement parsing pipeline fails."""


def parse_financial_statement(file_path: str) -> dict[str, float]:
    """
    Parse a financial statement PDF into a normalized financial data dictionary.

    Workflow:
        1. Extract text from the PDF via ``extract_text_from_pdf``
        2. Identify line items via ``extract_financial_data``
        3. Normalize labels via ``normalize_financial_data``
        4. Return the normalized dictionary (None values omitted)

    Args:
        file_path: Path to the financial statement PDF.

    Returns:
        Normalized financial data, for example::

            {
                "revenue": 1000000.0,
                "cogs": 600000.0,
                "gross_profit": 400000.0,
                "opex": 150000.0,
                "cash": 200000.0,
            }

    Raises:
        FinancialStatementParseError: If ``file_path`` is invalid, the PDF has
            no extractable text, extraction/normalization fails, or no
            recognized financial fields are found.
        PDFReadError: If the PDF cannot be opened or read.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        raise FinancialStatementParseError(
            "file_path must be a non-empty string."
        )

    try:
        text = extract_text_from_pdf(file_path)
    except PDFReadError:
        raise
    except Exception as exc:
        raise FinancialStatementParseError(
            f"Failed to extract text from PDF: {file_path}"
        ) from exc

    if not text.strip():
        raise FinancialStatementParseError(
            f"No extractable text found in PDF: {file_path}"
        )

    try:
        raw_data = extract_financial_data(text)
        normalized = normalize_financial_data(raw_data)
    except FinancialStatementParseError:
        raise
    except Exception as exc:
        raise FinancialStatementParseError(
            f"Failed to extract or normalize financial data from PDF: {file_path}"
        ) from exc

    result: dict[str, float] = {
        key: value
        for key, value in normalized.items()
        if value is not None
    }

    if not result:
        raise FinancialStatementParseError(
            f"No recognized financial fields found in PDF: {file_path}"
        )

    return result
