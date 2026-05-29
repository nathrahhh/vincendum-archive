import { request } from "./client";
import type { BreachesByIndustry } from "../types";

/** GET /breaches */
export function fetchBreaches(): Promise<BreachesByIndustry> {
  return request<BreachesByIndustry>("/breaches");
}
