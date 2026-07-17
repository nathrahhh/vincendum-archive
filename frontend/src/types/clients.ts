export type ClientDeal = {
  id: number;
  name: string;
  value: number;
  industry: string;
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
};

export type ClientFinancials = {
  client_id: number;
  historical: ClientFinancialRecord[];
};

export type ForecastAssumptions = {
  revenue_growth_rate: number;
  average_cogs_ratio: number;
  average_opex_ratio: number;
  average_gross_margin: number | null;
};

export type ForecastHistoricalRecord = {
  month: string;
  revenue: number;
  cogs: number;
  opex: number;
  reported_gross_profit: number | null;
  calculated_gross_profit: number;
  cash_balance: number;
};

export type ProphetForecastRecord = {
  month: string;
  revenue: number;
  gross_profit: number;
  base: number;
  best: number;
  worst: number;
  lower_bound: number;
  upper_bound: number;
};

export type ProphetHistoricalRecord = {
  month: string;
  revenue: number;
  gross_profit: number;
};

export type ProphetForecast = {
  client_id: number;
  model_type: "prophet";
  historical: ProphetHistoricalRecord[];
  forecast: ProphetForecastRecord[];
};

export type DeterministicForecastRecord = {
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

export type DeterministicForecastAlerts = {
  gross_profit_alerts: {
    month: string;
    message: string;
    difference_pct: number;
  }[];
};

export type DeterministicForecast = {
  client_id: number;
  model_type: "deterministic";
  assumptions: ForecastAssumptions;
  historical: ForecastHistoricalRecord[];
  forecast: DeterministicForecastRecord[];
  alerts: DeterministicForecastAlerts;
};

/** @deprecated Prefer DeterministicForecastRecord */
export type ForecastRecord = DeterministicForecastRecord;

export type ClientForecast = ProphetForecast | DeterministicForecast;

export type ClientForecastScenarios = {
  base: ClientForecast;
  best: ClientForecast;
  worst: ClientForecast;
};

export type ClientFinancialCreate = {
  client_id: number;
  month: string;
  revenue: number;
  cogs: number;
  opex: number;
  cash_balance: number;
  gross_profit: number;
};

export type ClientFinancialCreateResponse = {
  message: string;
  record: {
    id: number;
    client_id: number;
    month: string;
    revenue: number;
    cogs: number;
    opex: number;
    cash_balance: number;
    gross_profit: number;
  };
};
