import { request } from "./client";
import type { ClientApplicationCreate, ClientApplicationCreateResponse } from "../types";

export function postClientApplication(
  payload: ClientApplicationCreate,
): Promise<ClientApplicationCreateResponse> {
  return request<ClientApplicationCreateResponse>("/client-applications", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
