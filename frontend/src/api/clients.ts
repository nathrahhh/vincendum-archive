import { request } from "./client";
import type { Client, ClientFinancials, ClientForecast } from "../types";

export function fetchClients(): Promise<Client[]> {
  return request<Client[]>("/clients");
}

export function fetchClientFinancials(clientId: number): Promise<ClientFinancials> {
  return request<ClientFinancials>(`/clients/${clientId}/financials`);
}

export function fetchClientForecast(clientId: number): Promise<ClientForecast> {
  return request<ClientForecast>(`/clients/${clientId}/forecast`);
}
