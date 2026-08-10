import { request } from "./client";
import type {
  Client,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancials,
  ClientForecast,
  ClientInvitation,
  ForecastModel,
  ProphetForecastResponse,
} from "../types";

export function fetchClients(): Promise<Client[]> {
  return request<Client[]>("/clients");
}

export function fetchClient(clientId: number): Promise<Client> {
  return request<Client>(`/clients/${clientId}`);
}

export function fetchClientFinancials(clientId: number): Promise<ClientFinancials> {
  return request<ClientFinancials>(`/clients/${clientId}/financials`);
}

export function fetchClientForecast(
  clientId: number,
  revenueGrowthRate: number,
  model: ForecastModel = "deterministic",
): Promise<ClientForecast | ProphetForecastResponse> {
  const params = new URLSearchParams({
    model,
  });

  if (model === "deterministic") {
    params.set("revenue_growth_rate", String(revenueGrowthRate));
  }

  return request<ClientForecast | ProphetForecastResponse>(
    `/clients/${clientId}/forecast?${params.toString()}`,
  );
}

export function postClientFinancial(
  payload: ClientFinancialCreate,
): Promise<ClientFinancialCreateResponse> {
  return request<ClientFinancialCreateResponse>("/client-financials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateClientCreditLimit(
  clientId: number,
  creditLimit: number,
): Promise<Client> {
  return request<Client>(`/clients/${clientId}/credit-limit`, {
    method: "PUT",
    body: JSON.stringify({ credit_limit: creditLimit }),
  });
}

export function postClientInvite(
  clientId: number,
  email: string,
): Promise<ClientInvitation> {
  return request<ClientInvitation>(`/clients/${clientId}/invite`, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}
