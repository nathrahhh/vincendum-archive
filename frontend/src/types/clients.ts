export type Client = {
  id: number;
  name: string;
  industry: string;
  credit_limit: number;
};

export type ClientFinancials = {
  client_id: number;
  labels: string[];
  revenue: number[];
  cogs: number[];
  opex: number[];
  cash_balance: number[];
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
