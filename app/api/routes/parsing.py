import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.financial_extraction import FinancialStatementExtraction
from app.services.parsing.parser import (
    FinancialStatementParseError,
    parse_uploaded_financial_statement,
)
from app.services.parsing.pdf_reader import PDFReadError

router = APIRouter(prefix="/parsing", tags=["parsing"])

SUPPORTED_EXTENSIONS = {".pdf", ".csv"}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}


def _upload_extension(file: UploadFile) -> str | None:
    filename = (file.filename or "").strip()
    if not filename:
        return None
    extension = Path(filename).suffix.lower()
    return extension or None


def _is_supported_upload(file: UploadFile) -> bool:
    extension = _upload_extension(file)
    if extension in SUPPORTED_EXTENSIONS:
        return True

    content_type = (file.content_type or "").lower()
    return content_type in SUPPORTED_CONTENT_TYPES


def _resolve_temp_suffix(file: UploadFile) -> str:
    extension = _upload_extension(file)
    if extension in SUPPORTED_EXTENSIONS:
        return extension

    content_type = (file.content_type or "").lower()
    if content_type in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        return ".csv"
    if content_type in {"application/pdf", "application/x-pdf"}:
        return ".pdf"

    raise HTTPException(
        status_code=400,
        detail="Uploaded file must be a PDF or CSV.",
    )


@router.post(
    "/financial-statement",
    response_model=FinancialStatementExtraction,
)
async def parse_financial_statement_upload(
    file: UploadFile = File(...),
) -> FinancialStatementExtraction:
    """
    Accept a financial statement PDF or CSV upload and return extracted fields.
    """
    if not _is_supported_upload(file):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a PDF or CSV.",
        )

    temp_path: str | None = None

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded PDF or CSV file is empty.",
            )

        suffix = _resolve_temp_suffix(file)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        return parse_uploaded_financial_statement(temp_path)

    except HTTPException:
        raise
    except PDFReadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FinancialStatementParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse financial statement file.",
        ) from exc
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        await file.close()
