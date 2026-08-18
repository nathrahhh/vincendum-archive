import { request } from "../api/client";
import type { Lender, LenderOnboardRequest } from "../types/auth";
import { toServiceError } from "./errors";

export async function onboardLender(
  payload: LenderOnboardRequest,
): Promise<Lender> {
  try {
    return await request<Lender>("/lenders/onboard", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw toServiceError(error, "Failed to create lender");
  }
}

export async function fetchMyLender(): Promise<Lender> {
  try {
    return await request<Lender>("/lenders/me");
  } catch (error) {
    throw toServiceError(error, "Failed to load lender");
  }
}

export async function fetchPublicLender(slug: string): Promise<Lender> {
  try {
    return await request<Lender>(
      `/lenders/public/${encodeURIComponent(slug)}`,
    );
  } catch (error) {
    throw toServiceError(error, "Failed to load lender");
  }
}
