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

export type ForecastAssumptions = {
  revenue_growth_rate: number;
  average_cogs_ratio: number;
  average_opex_ratio: number;
  average_gross_margin: number;
};

export type ForecastHistoricalRecord = {
  month: string;
  revenue: number;
  cogs: number;
  opex: number;
  reported_gross_profit: number;
  calculated_gross_profit: number;
  cash_balance: number;
};

export type ForecastRecord = {
  month: string;
  revenue: number;
  cogs: number;
  opex: number;
  gross_profit_margin_method: number | null;
  gross_profit_cogs_method: number;
  gross_profit_difference: number | null;
  net_cash_flow: number;
  cash_balance: number;
};

export type ClientForecast = {
  client_id: number;
  assumptions: ForecastAssumptions;
  historical: ForecastHistoricalRecord[];
  forecast: ForecastRecord[];
};

export type ProphetForecastPoint = {
  month: string;
  revenue: number;
  lower_bound: number;
  upper_bound: number;
};

export type ProphetHistoricalPoint = {
  month: string;
  revenue: number;
};


export type ProphetForecastResponse = {
  client_id: number;
  model: "prophet";
  historical: ProphetHistoricalPoint[];
  forecast: ProphetForecastPoint[];
};

export type ForecastModel = "deterministic" | "prophet";

export type StatisticalForecastModelName =
  | "naive"
  | "seasonal_naive"
  | "ets"
  | "holt_winters"
  | "prophet";

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

export type ClientForecastScenarios = {
  base: ClientForecast;
  best: ClientForecast;
  worst: ClientForecast;
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
