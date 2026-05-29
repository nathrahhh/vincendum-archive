export type Position = {
  name: string;
  value: number;
  industry: string;
};

export type IndustryExposure = {
  industry: string;
  value: number;
  percentage: number;
};

export type PortfolioResponse = {
  positions: Position[];
  total_portfolio_value: number;
  capital_utilization_pct: number;
  industry_exposure: IndustryExposure[];
};
