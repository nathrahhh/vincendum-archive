import {
  fetchClient,
  fetchClientFinancials,
  fetchClientForecast,
  fetchClients,
  postClientApplication,
  postClientFinancial,
  updateClientCreditLimit as putClientCreditLimit,
} from "../api";
import type {
  Client,
  ClientApplicationCreate,
  ClientApplicationCreateResponse,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancials,
  ClientForecast,
  ClientForecastScenarios,
  ForecastModel,
  ProphetForecastResponse,
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
  model: ForecastModel = "deterministic",
): Promise<ClientForecast | ProphetForecastResponse> {
  try {
    return await fetchClientForecast(clientId, revenueGrowthRate, model);
  } catch (error) {
    throw toServiceError(error, "Failed to load client forecast");
  }
}

export async function getClientForecastScenarios(
  clientId: number,
  baseGrowthRate: number,
  bestGrowthRate: number,
  worstGrowthRate: number,
): Promise<ClientForecastScenarios> {
  try {
    const [base, best, worst] = await Promise.all([
      fetchClientForecast(clientId, baseGrowthRate, "deterministic"),
      fetchClientForecast(clientId, bestGrowthRate, "deterministic"),
      fetchClientForecast(clientId, worstGrowthRate, "deterministic"),
    ]);
    return {
      base: base as ClientForecast,
      best: best as ClientForecast,
      worst: worst as ClientForecast,
    };
  } catch (error) {
    throw toServiceError(error, "Failed to load forecast scenarios");
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
