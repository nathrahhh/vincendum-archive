from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.financial_extraction import FinancialStatementExtraction

client = TestClient(app)

MOCK_FINANCIAL_DATA = FinancialStatementExtraction(
    revenue=1_000_000.0,
    cogs=600_000.0,
    gross_profit=400_000.0,
    opex=150_000.0,
    cash=200_000.0,
    assets=900_000.0,
    liabilities=500_000.0,
    equity=400_000.0,
)


def test_parse_financial_statement_pdf_success():
    with patch(
        "app.api.routes.parsing.parse_uploaded_financial_statement",
        return_value=MOCK_FINANCIAL_DATA,
    ) as mock_parse:
        response = client.post(
            "/parsing/financial-statement",
            files={
                "file": ("statement.pdf", b"%PDF-1.4 fake content", "application/pdf"),
            },
        )

    assert response.status_code == 200

    payload = response.json()
    assert payload["revenue"] == 1_000_000.0
    assert payload["cogs"] == 600_000.0
    assert payload["gross_profit"] == 400_000.0
    assert payload["opex"] == 150_000.0
    assert payload["cash"] == 200_000.0

    mock_parse.assert_called_once()
    (temp_path,) = mock_parse.call_args.args
    assert isinstance(temp_path, str)
    assert temp_path.endswith(".pdf")


def test_parse_financial_statement_csv_success():
    with patch(
        "app.api.routes.parsing.parse_uploaded_financial_statement",
        return_value=MOCK_FINANCIAL_DATA,
    ) as mock_parse:
        response = client.post(
            "/parsing/financial-statement",
            files={
                "file": ("statement.csv", b"revenue,cogs\n100,60\n", "text/csv"),
            },
        )

    assert response.status_code == 200
    assert response.json()["revenue"] == 1_000_000.0

    mock_parse.assert_called_once()
    (temp_path,) = mock_parse.call_args.args
    assert temp_path.endswith(".csv")


def test_parse_financial_statement_xlsx_success():
    with patch(
        "app.api.routes.parsing.parse_uploaded_financial_statement",
        return_value=MOCK_FINANCIAL_DATA,
    ) as mock_parse:
        response = client.post(
            "/parsing/financial-statement",
            files={
                "file": (
                    "statement.xlsx",
                    b"PK fake xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )

    assert response.status_code == 200
    assert response.json()["revenue"] == 1_000_000.0

    mock_parse.assert_called_once()
    (temp_path,) = mock_parse.call_args.args
    assert temp_path.endswith(".xlsx")


def test_parse_financial_statement_rejects_unsupported_type():
    with patch(
        "app.api.routes.parsing.parse_uploaded_financial_statement",
    ) as mock_parse:
        response = client.post(
            "/parsing/financial-statement",
            files={
                "file": ("notes.txt", b"not a statement", "text/plain"),
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be a PDF, CSV, or XLSX."
    mock_parse.assert_not_called()
