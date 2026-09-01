export type PortfolioRecord = {
  id: number;
  name: string;
  lender_id: number;
  capital_allocation: number;
};

export type PortfolioSummary = {
  portfolio_id: number;
  portfolio_name: string;
  capital_allocation: number;
  total_exposure: number;
  position_count: number;
  client_count: number;
  utilization_pct: number;
};

export type PortfolioCreateRequest = {
  name: string;
  capital_allocation: number;
};

export type PortfolioUpdateRequest = {
  name?: string;
  capital_allocation?: number;
};

export type IndustryExposure = {
  industry: string;
  value: number;
  percentage: number;
};
