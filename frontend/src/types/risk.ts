export type Breach = {
  rule: string;
  limit_pct: number;
  actual_pct: number;
  detail: string;
};

/** GET /breaches and resolve response — persisted breach record */
export type BreachRecord = {
  id: number;
  client_id: number;
  reason: string;
  rule: string;
  threshold: number;
  actual_value: number;
  detail: string;
  status: string;
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
