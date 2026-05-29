import { fetchPortfolio } from "../api";
import type { Position } from "../types";
import { toServiceError } from "./errors";

/** GET /portfolio */
export async function getPortfolio(): Promise<Position[]> {
  try {
    return await fetchPortfolio();
  } catch (error) {
    throw toServiceError(error, "Failed to load portfolio");
  }
}
