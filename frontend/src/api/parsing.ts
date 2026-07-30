import type { FinancialStatementExtraction } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE;

export async function postFinancialStatementExtract(
  file: File,
): Promise<FinancialStatementExtraction> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/financials/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
