import { request } from "./client";
import type {
  PortfolioCreateRequest,
  PortfolioRecord,
  PortfolioSummary,
  PortfolioUpdateRequest,
} from "../types/portfolio";

/** GET /portfolios */
export function fetchPortfolios(): Promise<PortfolioRecord[]> {
  return request<PortfolioRecord[]>("/portfolios");
}

/** POST /portfolios */
export function createPortfolio(
  payload: PortfolioCreateRequest,
): Promise<PortfolioRecord> {
  return request<PortfolioRecord>("/portfolios", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** GET /portfolios/{portfolio_id} */
export function fetchPortfolio(portfolioId: number): Promise<PortfolioSummary> {
  return request<PortfolioSummary>(`/portfolios/${portfolioId}`);
}

/** PATCH /portfolios/{portfolio_id} */
export function updatePortfolio(
  portfolioId: number,
  payload: PortfolioUpdateRequest,
): Promise<PortfolioRecord> {
  return request<PortfolioRecord>(`/portfolios/${portfolioId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
