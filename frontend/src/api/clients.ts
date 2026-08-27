import { request } from "./client";
import type {
  Client,
  ClientFinancialCreate,
  ClientFinancialCreateResponse,
  ClientFinancialRecord,
  ClientFinancials,
  ClientForecast,
  ClientInvitation,
  ForecastModel,
  ForecastBacktestResponse,
  ProphetForecastResponse,
} from "../types";

export function fetchClients(): Promise<Client[]> {
  return request<Client[]>("/clients");
}

export function fetchClient(clientId: number): Promise<Client> {
  return request<Client>(`/clients/${clientId}`);
}

/** GET /clients/{client_id}/financials — admin list for a client */
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

/** GET /clients/{client_id}/forecast/backtest */
export function fetchClientForecastBacktest(
  clientId: number,
): Promise<ForecastBacktestResponse> {
  return request<ForecastBacktestResponse>(
    `/clients/${clientId}/forecast/backtest`,
  );
}

/** POST /client/me/financials */
export function postClientFinancial(
  payload: ClientFinancialCreate,
): Promise<ClientFinancialCreateResponse> {
  return request<ClientFinancialCreateResponse>("/client/me/financials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** POST /client-financials/{id}/approve */
export function postApproveClientFinancial(
  id: number,
): Promise<ClientFinancialRecord> {
  return request<ClientFinancialRecord>(`/client-financials/${id}/approve`, {
    method: "POST",
  });
}

/** POST /client-financials/{id}/reject */
export function postRejectClientFinancial(
  id: number,
): Promise<ClientFinancialRecord> {
  return request<ClientFinancialRecord>(`/client-financials/${id}/reject`, {
    method: "POST",
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

export function fetchMyClient(): Promise<Client> {
  return request<Client>("/client/me");
}

export function fetchMyClientFinancials(): Promise<ClientFinancials> {
  return request<ClientFinancials>("/client/me/financials");
}

export function fetchMyClientForecast(
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
    `/client/me/forecast?${params.toString()}`,
  );
}

/** GET /client/me/forecast/backtest */
export function fetchMyClientForecastBacktest(): Promise<ForecastBacktestResponse> {
  return request<ForecastBacktestResponse>("/client/me/forecast/backtest");
}

export function fetchMyClientDeals(): Promise<
  Array<{
    id: number;
    client_id: number | null;
    name: string;
    value: number;
    industry: string;
    status: string | null;
  }>
> {
  return request("/client/me/deals");
}
