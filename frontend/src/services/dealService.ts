import { postEvaluateDeal } from "../api";
import type { DealPayload, RiskEvaluation } from "../types";
import { toServiceError } from "./errors";

/** POST /deals/evaluate */
export async function evaluateDeal(deal: DealPayload): Promise<RiskEvaluation> {
  try {
    return await postEvaluateDeal(deal);
  } catch (error) {
    throw toServiceError(error, "Failed to evaluate deal");
  }
}
