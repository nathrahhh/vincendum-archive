import { fetchClientFinancials, fetchClientForecast, fetchClients } from "../api";
import type { Client, ClientFinancials, ClientForecast } from "../types";
import { toServiceError } from "./errors";

export async function getClients(): Promise<Client[]> {
  try {
    return await fetchClients();
  } catch (error) {
    throw toServiceError(error, "Failed to load clients");
  }
}

export async function getClientFinancials(clientId: number): Promise<ClientFinancials> {
  try {
    return await fetchClientFinancials(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client financials");
  }
}

export async function getClientForecast(clientId: number): Promise<ClientForecast> {
  try {
    return await fetchClientForecast(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client forecast");
  }
}
