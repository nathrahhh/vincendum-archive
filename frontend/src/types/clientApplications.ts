export type ClientApplicationRecord = {
  id: number;
  name: string;
  industry: string;
  credit_limit: number;
  status: string;
  created_at?: string;
};

export type ClientApplicationCreate = {
  name: string;
  industry: string;
  credit_limit: number;
};

export type ClientApplicationCreateResponse = {
  message: string;
  application?: ClientApplicationRecord;
  reasons?: string[];
};

export type ClientApplicationApproveResponse = {
  message: string;
  client: {
    id: number;
    name: string;
    industry: string;
    credit_limit: number;
  };
};

export type ClientApplicationRejectResponse = {
  message: string;
  application: ClientApplicationRecord;
};
