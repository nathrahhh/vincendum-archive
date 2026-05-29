import { fetchPortfolio } from "../api";
import type { PortfolioResponse } from "../types";
import { toServiceError } from "./errors";

/** GET /portfolio */
export async function getPortfolio(): Promise<PortfolioResponse> {
  try {
    return await fetchPortfolio();
  } catch (error) {
    throw toServiceError(error, "Failed to load portfolio");
  }
}
