import { useId, useState, type ChangeEvent } from "react";
import { extractFinancialStatement } from "../../services";
import type { FinancialStatementExtraction } from "../../types";

const ACCEPTED_EXTENSIONS = [".pdf", ".csv", ".xlsx"] as const;
const ACCEPT_ATTR =
  ".pdf,.csv,.xlsx,application/pdf,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

const FIELD_LABELS: { key: keyof FinancialStatementExtraction; label: string }[] = [
  { key: "revenue", label: "Revenue" },
  { key: "cogs", label: "COGS" },
  { key: "gross_profit", label: "Gross Profit" },
  { key: "opex", label: "OPEX" },
  { key: "cash", label: "Cash" },
  { key: "assets", label: "Assets" },
  { key: "liabilities", label: "Liabilities" },
  { key: "equity", label: "Equity" },
];

type FinancialStatementUploadProps = {
  onExtract: (data: FinancialStatementExtraction) => void;
};

function isAllowedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

function formatValue(value: number | null): string {
  if (value === null) {
    return "—";
  }
  return value.toLocaleString();
}

export default function FinancialStatementUpload({
  onExtract,
}: FinancialStatementUploadProps) {
  const inputId = useId();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extracted, setExtracted] = useState<FinancialStatementExtraction | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setError(null);
    setExtracted(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!isAllowedFile(file)) {
      setSelectedFile(null);
      setError("Only PDF, CSV, and Excel (.xlsx) files are allowed.");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  }

  async function handleExtract() {
    if (!selectedFile || isExtracting) {
      return;
    }

    setIsExtracting(true);
    setError(null);

    try {
      const data = await extractFinancialStatement(selectedFile);
      setExtracted(data);
      onExtract(data);
    } catch (err) {
      setExtracted(null);
      setError(
        err instanceof Error ? err.message : "Failed to extract financial statement",
      );
    } finally {
      setIsExtracting(false);
    }
  }

  return (
    <div className="deal-form">
      <h2 className="deal-form__title">Financial Statement Upload</h2>
      <p className="deal-form__subtitle">
        Upload a PDF, CSV, or Excel statement to extract financial values
      </p>

      <label className="deal-form__field" htmlFor={inputId}>
        <span className="deal-form__label">Statement file</span>
        <input
          id={inputId}
          className="deal-form__input"
          type="file"
          accept={ACCEPT_ATTR}
          onChange={handleFileChange}
          disabled={isExtracting}
        />
      </label>

      {selectedFile ? (
        <p className="clients-panel__hint">Selected: {selectedFile.name}</p>
      ) : null}

      <button
        className="deal-form__submit"
        type="button"
        onClick={handleExtract}
        disabled={!selectedFile || isExtracting}
      >
        {isExtracting ? "Extracting…" : "Extract Values"}
      </button>

      {error ? <p className="dashboard-error">{error}</p> : null}

      {extracted ? (
        <div className="deal-form__section">
          <h3 className="deal-form__section-title">Extracted Values</h3>
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {FIELD_LABELS.map(({ key, label }) => (
                  <tr key={key}>
                    <td>{label}</td>
                    <td>{formatValue(extracted[key])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
