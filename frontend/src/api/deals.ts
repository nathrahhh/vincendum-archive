import { request } from "./client";
import type { DealApprovalPayload, DealPayload, DealRecord } from "../types";

/** GET /deals */
export function fetchDeals(): Promise<DealRecord[]> {
  return request<DealRecord[]>("/deals");
}

/** GET /clients/{clientId}/deals */
export function fetchClientDeals(clientId: number): Promise<DealRecord[]> {
  return request<DealRecord[]>(`/clients/${clientId}/deals`);
}

/** POST /deals/{id}/approve */
export function postApproveDeal(
  id: number,
  payload: DealApprovalPayload,
): Promise<DealRecord> {
  return request<DealRecord>(`/deals/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** POST /deals/{id}/reject */
export function postRejectDeal(id: number): Promise<DealRecord> {
  return request<DealRecord>(`/deals/${id}/reject`, { method: "POST" });
}

/** POST /client/me/deals */
export function postMyClientDeal(deal: DealPayload): Promise<DealRecord> {
  return request<DealRecord>("/client/me/deals", {
    method: "POST",
    body: JSON.stringify(deal),
  });
}
