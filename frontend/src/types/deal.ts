export type DealPayload = {
  name: string;
  value: number;
  term_months: number;
};

export type DealApprovalPayload = {
  principal_amount: number;
  interest_rate: number;
  interest_rate_type: string;
  repayment_method: string;
  term_months: number;
  start_date: string;
  payment_frequency: string;
  first_payment_date: string;
  maturity_date: string | null;
};

export type DealRecord = {
  id: number;
  client_id: number;
  name: string;
  value: number;
  status: string | null;
  principal_amount: number | null;
  interest_rate: number | null;
  interest_rate_type: string | null;
  repayment_method: string | null;
  term_months: number | null;
  start_date: string | null;
  maturity_date: string | null;
  payment_frequency: string | null;
  first_payment_date: string | null;
};
