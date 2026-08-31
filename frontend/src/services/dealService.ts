import { fetchDeals, postApproveDeal, postMyClientDeal, postRejectDeal } from "../api";
import type { DealApprovalPayload, DealPayload, DealRecord } from "../types";
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
export async function approveDeal(
  id: number,
  payload: DealApprovalPayload,
): Promise<DealRecord> {
  try {
    return await postApproveDeal(id, payload);
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

/** POST /client/me/deals */
export async function createMyDeal(deal: DealPayload): Promise<DealRecord> {
  try {
    return await postMyClientDeal(deal);
  } catch (error) {
    throw toServiceError(error, "Failed to submit deal");
  }
}
