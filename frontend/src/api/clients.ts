import { request } from "./client";
import type {
  Client,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancials,
  ClientForecast,
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

export function fetchClientForecast(clientId: number): Promise<ClientForecast> {
  return request<ClientForecast>(`/clients/${clientId}/forecast`);
}

export function postClientFinancial(
  payload: ClientFinancialCreate,
): Promise<ClientFinancialCreateResponse> {
  return request<ClientFinancialCreateResponse>("/client-financials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
