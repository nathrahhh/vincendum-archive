import { fetchCurrentUser } from "../api/users";
import type { CurrentUser } from "../types/auth";
import { toServiceError } from "./errors";

export async function getCurrentUser(): Promise<CurrentUser> {
  try {
    return await fetchCurrentUser();
  } catch (error) {
    throw toServiceError(error, "Failed to load current user");
  }
}
