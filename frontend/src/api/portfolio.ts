import { request } from "./client";
import type { Position } from "../types";

/** GET /portfolio */
export function fetchPortfolio(): Promise<Position[]> {
  return request<Position[]>("/portfolio");
}
