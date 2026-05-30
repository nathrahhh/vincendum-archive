import { request } from "./client";
import type { DealPayload, DealRecord, RiskEvaluation } from "../types";

/** GET /deals */
export function fetchDeals(): Promise<DealRecord[]> {
  return request<DealRecord[]>("/deals");
}

/** POST /deals/evaluate */
export function postEvaluateDeal(deal: DealPayload): Promise<RiskEvaluation> {
  return request<RiskEvaluation>("/deals/evaluate", {
    method: "POST",
    body: JSON.stringify(deal),
  });
}
