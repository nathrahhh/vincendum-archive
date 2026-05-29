export type Breach = {
  rule: string;
  limit_pct: number;
  actual_pct: number;
  detail: string;
};

export type BreachRecord = Breach & {
  id?: number;
  reason?: string;
};

/** GET /breaches — grouped by industry */
export type BreachesByIndustry = Record<string, BreachRecord[]>;

export type RiskEvaluation = {
  status: string;
  portfolio_value: number;
  capital_utilization_pct: number;
  industry_exposure: Record<string, number>;
  breaches: Breach[];
};
