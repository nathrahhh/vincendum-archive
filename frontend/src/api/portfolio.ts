import { request } from "./client";
import type { PortfolioResponse } from "../types";

/** GET /portfolio */
export function fetchPortfolio(): Promise<PortfolioResponse> {
  return request<PortfolioResponse>("/portfolio");
}
