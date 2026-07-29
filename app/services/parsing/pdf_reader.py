"""PDF text extraction utilities."""

from pathlib import Path

import pdfplumber


class PDFReadError(Exception):
    """Raised when a PDF file cannot be opened or read."""


def extract_text_from_pdf(file_path: str) -> str:
    """
    Read a PDF file and return its extracted plain text.

    Opens the PDF with pdfplumber, extracts text from every page that
    contains content, and concatenates the results with newlines.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text content from pages that contain extractable text.
        Returns an empty string if the PDF has no extractable text.

    Raises:
        PDFReadError: If the file does not exist or cannot be opened as a PDF.
    """
    path = Path(file_path)

    if not path.is_file():
        raise PDFReadError(f"PDF file not found: {file_path}")

    try:
        with pdfplumber.open(path) as pdf:
            page_texts: list[str] = []

            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    page_texts.append(text.strip())

            return "\n".join(page_texts)
    except PDFReadError:
        raise
    except Exception as exc:
        raise PDFReadError(f"Unable to open or read PDF: {file_path}") from exc
