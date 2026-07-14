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
