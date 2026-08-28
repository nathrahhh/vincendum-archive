export type ClientDeal = {
  id: number;
  name: string;
  value: number;
  status: string;
};

export type Client = {
  id: number;
  name: string;
  industry: string;
  credit_limit: number;
  current_exposure?: number;
  remaining_credit?: number;
  utilization_pct?: number;
  deal_count?: number;
  deals?: ClientDeal[];
};

export type ClientFinancialRecord = {
  id: number;
  client_id: number;
  month: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  opex: number;
  cash_balance: number;
  status: "PENDING" | "APPROVED" | "REJECTED";
};

export type ClientFinancials = {
  client_id: number;
  historical: ClientFinancialRecord[];
};

export type StatisticalForecastModelName =
  | "naive"
  | "seasonal_naive"
  | "ets"
  | "holt_winters"
  | "prophet";

export type ForecastRevenuePoint = {
  month: string;
  revenue: number;
};

export type ProphetForecastPoint = {
  month: string;
  revenue: number;
  lower_bound?: number;
  upper_bound?: number;
};

export type ProphetHistoricalPoint = {
};

export type ProphetForecastResponse = {
  client_id: number;
  model: "prophet";
  historical: ProphetHistoricalPoint[];
  forecast: ProphetForecastPoint[];
  unavailable_reason?: string | null;
};

export type StatisticalForecastResponse = {
  client_id: number;
  model: StatisticalForecastModelName;
  historical: ForecastRevenuePoint[];
  forecast: ForecastRevenuePoint[];
  unavailable_reason: string | null;
};

export type ForecastModel = "deterministic" | StatisticalForecastModelName;

export type ForecastBacktestResult = {
  model: StatisticalForecastModelName | string;
  mae: number | null;
  available: boolean;
  unavailable_reason: string | null;
};

export type ForecastBacktestResponse = {
  client_id: number;
  metric: "mae";
  holdout_months: number;
  best_model: StatisticalForecastModelName | null;
  results: ForecastBacktestResult[];
};

export type ClientFinancialCreate = {
  month: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  opex: number;
  cash_balance: number;
};

export type ClientFinancialCreateResponse = {
  message: string;
  record: {
    id: number;
    client_id: number;
    month: string;
    revenue: number;
    cogs: number;
    gross_profit: number;
    opex: number;
    cash_balance: number;
    status: "PENDING" | "APPROVED" | "REJECTED";
  };
};

export type ClientInvitation = {
  id: number;
  client_id: number;
  email: string;
  status: string;
  expires_at: string;
  token: string;
  invitation_url: string;
};
