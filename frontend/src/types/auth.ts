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
};

export type LenderOnboardRequest = {
  name: string;
};
