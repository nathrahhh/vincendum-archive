import { request } from "../api/client";
import type {
  ClientApplicationApproveResponse,
  ClientApplicationCreate,
  ClientApplicationCreateResponse,
  ClientApplicationRecord,
  ClientApplicationRejectResponse,
} from "../types/clientApplications";
import { toServiceError } from "./errors";

export async function postClientApplication(
  payload: ClientApplicationCreate,
): Promise<ClientApplicationCreateResponse> {
  try {
    return await request<ClientApplicationCreateResponse>("/client-applications", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw toServiceError(error, "Failed to submit application");
  }
}

export async function fetchClientApplications(): Promise<ClientApplicationRecord[]> {
  try {
    return await request<ClientApplicationRecord[]>("/client-applications");
  } catch (error) {
    throw toServiceError(error, "Failed to load client applications");
  }
}

export async function approveClientApplication(
  id: number,
): Promise<ClientApplicationApproveResponse> {
  try {
    return await request<ClientApplicationApproveResponse>(`/client-applications/${id}/approve`, {
      method: "POST",
    });
  } catch (error) {
    throw toServiceError(error, "Failed to approve application");
  }
}

export async function rejectClientApplication(
  id: number,
): Promise<ClientApplicationRejectResponse> {
  try {
    return await request<ClientApplicationRejectResponse>(`/client-applications/${id}/reject`, {
      method: "POST",
    });
  } catch (error) {
    throw toServiceError(error, "Failed to reject application");
  }
}
