import {
  fetchClient,
  fetchClientFinancials,
  fetchClientForecast,
  fetchClients,
  postClientApplication,
  postClientFinancial,
} from "../api";
import type {
  Client,
  ClientApplicationCreate,
  ClientApplicationCreateResponse,
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

export async function getClient(clientId: number): Promise<Client> {
  try {
    return await fetchClient(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client");
  }
}

export async function getClientFinancials(clientId: number): Promise<ClientFinancials> {
  try {
    return await fetchClientFinancials(clientId);
  } catch (error) {
    throw toServiceError(error, "Failed to load client financials");
  }
}

export async function getClientForecast(
  clientId: number,
  revenueGrowthRate: number,
): Promise<ClientForecast> {
  try {
    return await fetchClientForecast(clientId, revenueGrowthRate);
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

export async function submitClientApplication(
  payload: ClientApplicationCreate,
): Promise<ClientApplicationCreateResponse> {
  try {
    return await postClientApplication(payload);
  } catch (error) {
    throw toServiceError(error, "Failed to submit application");
  }
}
