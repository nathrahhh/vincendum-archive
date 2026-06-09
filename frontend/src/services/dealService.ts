import { fetchDeals, postApproveDeal, postEvaluateDeal, postRejectDeal } from "../api";
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

/** POST /deals/{id}/approve */
export async function approveDeal(id: number): Promise<DealRecord> {
  try {
    return await postApproveDeal(id);
  } catch (error) {
    throw toServiceError(error, "Failed to approve deal");
  }
}

/** POST /deals/{id}/reject */
export async function rejectDeal(id: number): Promise<DealRecord> {
  try {
    return await postRejectDeal(id);
  } catch (error) {
    throw toServiceError(error, "Failed to reject deal");
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
