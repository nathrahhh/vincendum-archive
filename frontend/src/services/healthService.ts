import { fetchHealth } from "../api";
import type { HealthResponse } from "../types";

/** Service layer for health checks. */
export function checkHealth(): Promise<HealthResponse> {
  return fetchHealth();
}
