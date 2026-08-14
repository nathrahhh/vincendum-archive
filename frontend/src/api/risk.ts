import { request } from "./client";
import type { BreachRecord, BreachesByIndustry } from "../types";

/** GET /breaches */
export function fetchBreaches(): Promise<BreachesByIndustry> {
  return request<BreachesByIndustry>("/breaches");
}

/** POST /breaches/{breachId}/resolve */
export function postResolveBreach(breachId: number): Promise<BreachRecord> {
  return request<BreachRecord>(`/breaches/${breachId}/resolve`, {
    method: "POST",
  });
}
