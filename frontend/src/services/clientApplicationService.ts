import { request } from "../api/client";
import type {
  ApplicationDocumentUploadResponse,
  ClientApplicationApproveResponse,
  ClientApplicationCreate,
  ClientApplicationCreateResponse,
  ClientApplicationRecord,
  ClientApplicationRejectResponse,
  DocumentRecord,
} from "../types/clientApplications";
import { toServiceError } from "./errors";

export async function postClientApplication(
  lenderSlug: string,
  payload: ClientApplicationCreate,
): Promise<ClientApplicationCreateResponse> {
  try {
    return await request<ClientApplicationCreateResponse>(
      `/client-applications/public/${encodeURIComponent(lenderSlug)}`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  } catch (error) {
    throw toServiceError(error, "Failed to submit application");
  }
}

export async function requestApplicationDocumentUploadUrl(
  lenderSlug: string,
  applicationId: number,
  payload: { name: string; content_type: string },
): Promise<ApplicationDocumentUploadResponse> {
  try {
    return await request<ApplicationDocumentUploadResponse>(
      `/apply/${encodeURIComponent(lenderSlug)}/applications/${applicationId}/documents/upload-url`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  } catch (error) {
    throw toServiceError(error, "Failed to prepare document upload");
  }
}

export async function fetchApplicationDocuments(
  lenderSlug: string,
  applicationId: number,
): Promise<DocumentRecord[]> {
  try {
    return await request<DocumentRecord[]>(
      `/apply/${encodeURIComponent(lenderSlug)}/applications/${applicationId}/documents`,
    );
  } catch (error) {
    throw toServiceError(error, "Failed to load application documents");
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
