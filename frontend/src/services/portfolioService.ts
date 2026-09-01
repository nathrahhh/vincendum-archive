import {
  createPortfolio as apiCreatePortfolio,
  fetchPortfolio as apiFetchPortfolio,
  fetchPortfolios as apiFetchPortfolios,
  updatePortfolio as apiUpdatePortfolio,
} from "../api/portfolio";
import type {
  PortfolioCreateRequest,
  PortfolioRecord,
  PortfolioSummary,
  PortfolioUpdateRequest,
} from "../types";
import { toServiceError } from "./errors";

/** GET /portfolios */
export async function fetchPortfolios(): Promise<PortfolioRecord[]> {
  try {
    return await apiFetchPortfolios();
  } catch (error) {
    throw toServiceError(error, "Failed to load portfolios");
  }
}

/** POST /portfolios */
export async function createPortfolio(
  payload: PortfolioCreateRequest,
): Promise<PortfolioRecord> {
  try {
    return await apiCreatePortfolio(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to create portfolio");
  }
}

/** GET /portfolios/{portfolio_id} */
export async function fetchPortfolio(
  portfolioId: number,
): Promise<PortfolioSummary> {
  try {
    return await apiFetchPortfolio(portfolioId);
  } catch (error) {
    throw toServiceError(error, "Failed to load portfolio");
  }
}

/** PATCH /portfolios/{portfolio_id} */
export async function updatePortfolio(
  portfolioId: number,
  payload: PortfolioUpdateRequest,
): Promise<PortfolioRecord> {
  try {
    return await apiUpdatePortfolio(portfolioId, payload);
  } catch (error) {
    throw toServiceError(error, "Failed to update portfolio");
  }
}
