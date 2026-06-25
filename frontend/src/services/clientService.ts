import {
  fetchClientFinancials,
  fetchClientForecast,
  fetchClients,
  postClientFinancial,
} from "../api";
import type {
  Client,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancials,
  ClientForecast,
} from "../types";
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

export async function submitClientFinancial(
  payload: ClientFinancialCreate,
): Promise<ClientFinancialCreateResponse> {
  try {
    return await postClientFinancial(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to submit client financials");
  }
}
