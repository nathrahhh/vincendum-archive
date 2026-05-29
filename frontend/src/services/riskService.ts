import { fetchBreaches } from "../api";
import type { BreachesByIndustry } from "../types";
import { toServiceError } from "./errors";

/** GET /breaches */
export async function getBreaches(): Promise<BreachesByIndustry> {
  try {
    return await fetchBreaches();
  } catch (error) {
    throw toServiceError(error, "Failed to load breaches");
  }
}
