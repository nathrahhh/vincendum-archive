import { fetchCurrentUser } from "../api/users";
import { postLenderOnboard } from "../api/lenders";
import type { CurrentUser, Lender, LenderOnboardRequest } from "../types/auth";
import { toServiceError } from "./errors";

export async function getCurrentUser(): Promise<CurrentUser> {
  try {
    return await fetchCurrentUser();
  } catch (error) {
    throw toServiceError(error, "Failed to load current user");
  }
}

export async function onboardLender(payload: LenderOnboardRequest): Promise<Lender> {
  try {
    return await postLenderOnboard(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to create lender");
  }
}
