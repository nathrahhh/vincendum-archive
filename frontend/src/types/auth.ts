export type CurrentUser = {
  id: number;
  email: string;
  role: string;
  lender_id: number | null;
  client_id: number | null;
};

export type Lender = {
  id: number;
  name: string;
  slug: string;
  capital_base: number;
};

export type LenderOnboardRequest = {
  name: string;
  capital_base: number;
};

export type LenderResponse = Lender;

export type LenderCapitalBaseUpdate = {
  capital_base: number;
};
