import { request } from "./client";
import type { CurrentUser } from "../types/auth";

export function fetchCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>("/users/me");
}
