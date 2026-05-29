import { request } from "./client";
import type { HealthResponse } from "../types";

/** GET / */
export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/");
}
