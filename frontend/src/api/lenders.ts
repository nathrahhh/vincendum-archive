import { request } from "./client";
import type { Lender, LenderOnboardRequest } from "../types/auth";

export function postLenderOnboard(payload: LenderOnboardRequest): Promise<Lender> {
  return request<Lender>("/lenders/onboard", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
