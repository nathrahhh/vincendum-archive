import { postFinancialStatementExtract } from "../api";
import type { FinancialStatementExtraction } from "../types";
import { toServiceError } from "./errors";

export async function extractFinancialStatement(
  file: File,
): Promise<FinancialStatementExtraction> {
  try {
    return await postFinancialStatementExtract(file);
  } catch (error) {
    throw toServiceError(error, "Failed to extract financial statement");
  }
}
