import {
  fetchClient,
  fetchClientDeals,
  fetchClientFinancials,
  fetchClientForecast,
  fetchClientForecastBacktest,
  fetchClients,
  fetchMyClient,
  fetchMyClientDeals,
  fetchMyClientFinancials,
  fetchMyClientForecast,
  fetchMyClientForecastBacktest,
  postClientApplication,
  postClientFinancial,
  postClientInvite,
  updateClientCreditLimit as putClientCreditLimit,
} from "../api";
import {
  postApproveClientFinancial,
  postRejectClientFinancial,
} from "../api/clients";
import { request } from "../api/client";
import type {
  Client,
  ClientApplicationCreate,
  ClientApplicationCreateResponse,
  ClientDeal,
  ClientDocumentDownloadResponse,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancialRecord,
  ClientFinancials,
  ClientForecast,
  ClientInvitation,
  DocumentRecord,
  ForecastBacktestResponse,
  ForecastModel,
  StatisticalForecastResponse,
} from "../types";
import { toServiceError } from "./errors";

export type { ClientInvitation };

export async function getClients(): Promise<Client[]> {
  try {
    return await fetchClients();
  } catch (error) {
    throw toServiceError(error, "Failed to load clients");
  }
}

export async function getClient(clientId: number): Promise<Client> {
  try {
    return await fetchClient(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client");
  }
}

/** GET /clients/{client_id}/financials — admin review list for a client */
export async function getClientFinancials(clientId: number): Promise<ClientFinancials> {
  try {
    return await fetchClientFinancials(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client financial submissions");
  }
}

export async function getClientDeals(clientId: number): Promise<ClientDeal[]> {
  try {
    const deals = await fetchClientDeals(clientId);

    return deals.map((deal) => ({
      id: deal.id,
      name: deal.name,
      value: deal.value,
      status: deal.status ?? "PENDING",
    }));
  } catch (error) {
    throw toServiceError(error, "Failed to load client deals");
  }
}

/** GET /clients/{client_id}/documents */
export async function fetchClientDocuments(
  clientId: number,
): Promise<DocumentRecord[]> {
  try {
    return await request<DocumentRecord[]>(`/clients/${clientId}/documents`);
  } catch (error) {
    throw toServiceError(error, "Failed to load client documents");
  }
}

/** GET /clients/{client_id}/documents/{document_id} */
export async function getClientDocument(
  clientId: number,
  documentId: number,
): Promise<ClientDocumentDownloadResponse> {
  try {
    return await request<ClientDocumentDownloadResponse>(
      `/clients/${clientId}/documents/${documentId}`,
    );
  } catch (error) {
    throw toServiceError(error, "Failed to load client document");
  }
}

/** GET /client/me/documents */
export async function fetchMyClientDocuments(): Promise<DocumentRecord[]> {
  try {
    return await request<DocumentRecord[]>("/client/me/documents");
  } catch (error) {
    throw toServiceError(error, "Failed to load your documents");
  }
}

/** GET /client/me/documents/{document_id} */
export async function getMyClientDocument(
  documentId: number,
): Promise<ClientDocumentDownloadResponse> {
  try {
    return await request<ClientDocumentDownloadResponse>(
      `/client/me/documents/${documentId}`,
    );
  } catch (error) {
    throw toServiceError(error, "Failed to load your document");
  }
}

export async function getClientForecast(
  clientId: number,
  revenueGrowthRate: number,
  model: ForecastModel = "deterministic",
): Promise<ClientForecast | StatisticalForecastResponse> {
  try {
    return await fetchClientForecast(clientId, revenueGrowthRate, model);
  } catch (error) {
    throw toServiceError(error, "Failed to load client forecast");
  }
}

export async function getClientForecastBacktest(
  clientId: number,
): Promise<ForecastBacktestResponse> {
  try {
    return await fetchClientForecastBacktest(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load forecast backtest");
  }
}

export async function submitClientFinancial(
  payload: ClientFinancialCreate,
): Promise<ClientFinancialCreateResponse> {
  try {
    return await postClientFinancial(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to submit client financials");
  }
}

/** POST /client-financials/{id}/approve */
export async function approveClientFinancial(
  id: number,
): Promise<ClientFinancialRecord> {
  try {
    return await postApproveClientFinancial(id);
  } catch (error) {
    throw toServiceError(error, "Failed to approve client financial submission");
  }
}

/** POST /client-financials/{id}/reject */
export async function rejectClientFinancial(
  id: number,
): Promise<ClientFinancialRecord> {
  try {
    return await postRejectClientFinancial(id);
  } catch (error) {
    throw toServiceError(error, "Failed to reject client financial submission");
  }
}

export async function submitClientApplication(
  payload: ClientApplicationCreate,
): Promise<ClientApplicationCreateResponse> {
  try {
    return await postClientApplication(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to submit application");
  }
}

export async function updateClientCreditLimit(
  clientId: number,
  creditLimit: number,
): Promise<Client> {
  try {
    return await putClientCreditLimit(clientId, creditLimit);
  } catch (error) {
    throw toServiceError(error, "Failed to update credit limit");
  }
}

export async function inviteClientUser(
  clientId: number,
  email: string,
): Promise<ClientInvitation> {
  try {
    return await postClientInvite(clientId, email);
  } catch (error) {
    throw toServiceError(error, "Failed to invite client user");
  }
}

export async function getMyClient(): Promise<Client> {
  try {
    return await fetchMyClient();
  } catch (error) {
    throw toServiceError(error, "Failed to load your client profile");
  }
}

export async function getMyClientFinancials(): Promise<ClientFinancials> {
  try {
    return await fetchMyClientFinancials();
  } catch (error) {
    throw toServiceError(error, "Failed to load your financials");
  }
}

export async function getMyClientForecast(
  revenueGrowthRate: number,
  model: ForecastModel = "deterministic",
): Promise<ClientForecast | StatisticalForecastResponse> {
  try {
    return await fetchMyClientForecast(revenueGrowthRate, model);
  } catch (error) {
    throw toServiceError(error, "Failed to load your forecast");
  }
}

export async function getMyClientForecastBacktest(): Promise<ForecastBacktestResponse> {
  try {
    return await fetchMyClientForecastBacktest();
  } catch (error) {
    throw toServiceError(error, "Failed to load your forecast backtest");
  }
}

export async function getMyClientDeals(): Promise<ClientDeal[]> {
  try {
    const deals = await fetchMyClientDeals();
    return deals.map((deal) => ({
      id: deal.id,
      name: deal.name,
      value: deal.value,
      status: deal.status ?? "PENDING",
    }));
  } catch (error) {
    throw toServiceError(error, "Failed to load your deals");
  }
}
