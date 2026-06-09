import { request } from "./client";
import type { DealPayload, DealRecord, RiskEvaluation } from "../types";

/** GET /deals */
export function fetchDeals(): Promise<DealRecord[]> {
  return request<DealRecord[]>("/deals");
}

/** POST /deals/{id}/approve */
export function postApproveDeal(id: number): Promise<DealRecord> {
  return request<DealRecord>(`/deals/${id}/approve`, { method: "POST" });
}

/** POST /deals/{id}/reject */
export function postRejectDeal(id: number): Promise<DealRecord> {
  return request<DealRecord>(`/deals/${id}/reject`, { method: "POST" });
}

/** POST /deals/evaluate */
export function postEvaluateDeal(deal: DealPayload): Promise<RiskEvaluation> {
  return request<RiskEvaluation>("/deals/evaluate", {
    method: "POST",
    body: JSON.stringify(deal),
  });
}
