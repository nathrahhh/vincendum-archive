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

export type ClientForecast = {
  client_id: number;
  historical: {
    labels: string[];
    cash_balance: number[];
    net_cash_flow: number[];
  };
  forecast: {
    labels: string[];
    cash_balance: number[];
  };
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
