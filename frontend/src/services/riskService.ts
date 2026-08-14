import { fetchBreaches, postResolveBreach } from "../api";
import type { BreachRecord, BreachesByIndustry } from "../types";
import { toServiceError } from "./errors";

/** GET /breaches */
export async function getBreaches(): Promise<BreachesByIndustry> {
  try {
    return await fetchBreaches();
  } catch (error) {
    throw toServiceError(error, "Failed to load breaches");
  }
}

/** POST /breaches/{breachId}/resolve */
export async function resolveBreach(breachId: number): Promise<BreachRecord> {
  try {
    return await postResolveBreach(breachId);
  } catch (error) {
    throw toServiceError(error, "Failed to resolve breach");
  }
}
