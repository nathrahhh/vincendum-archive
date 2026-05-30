import { fetchDeals, postEvaluateDeal } from "../api";
import type { DealPayload, DealRecord, RiskEvaluation } from "../types";
import { toServiceError } from "./errors";

/** GET /deals */
export async function getDeals(): Promise<DealRecord[]> {
  try {
    return await fetchDeals();
  } catch (error) {
    throw toServiceError(error, "Failed to load deals");
  }
}

/** POST /deals/evaluate */
export async function evaluateDeal(deal: DealPayload): Promise<RiskEvaluation> {
  try {
    return await postEvaluateDeal(deal);
  } catch (error) {
    throw toServiceError(error, "Failed to evaluate deal");
  }
}
