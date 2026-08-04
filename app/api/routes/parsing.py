from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pathlib import Path
import os
import tempfile

from app.auth.permissions import require_client
from app.models.user import UserORM
from app.schemas.financial_extraction import FinancialStatementExtraction
from app.services.parsing.parser import (
    FinancialStatementParseError,
    parse_uploaded_financial_statement,
)
from app.services.parsing.pdf_reader import PDFReadError

router = APIRouter(prefix="/parsing", tags=["parsing"])

SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".xlsx"}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

XLSX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}
PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
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
    if content_type in XLSX_CONTENT_TYPES:
        return ".xlsx"
    if content_type in CSV_CONTENT_TYPES:
        return ".csv"
    if content_type in PDF_CONTENT_TYPES:
        return ".pdf"

    raise HTTPException(
        status_code=400,
        detail="Uploaded file must be a PDF, CSV, or XLSX.",
    )


@router.post(
    "/financial-statement",
    response_model=FinancialStatementExtraction,
)
async def parse_financial_statement_upload(
    file: UploadFile = File(...),
) -> FinancialStatementExtraction:
    """
    Accept a financial statement PDF, CSV, or XLSX upload and return extracted fields.
    """
    if not _is_supported_upload(file):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a PDF, CSV, or XLSX.",
        )

    temp_path: str | None = None

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded PDF, CSV, or XLSX file is empty.",
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
        pass
        await file.close()
