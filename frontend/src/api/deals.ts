import { request } from "./client";
import type { DealPayload, RiskEvaluation } from "../types";

/** POST /deals/evaluate */
export function postEvaluateDeal(deal: DealPayload): Promise<RiskEvaluation> {
  return request<RiskEvaluation>("/deals/evaluate", {
    method: "POST",
    body: JSON.stringify(deal),
  });
}
