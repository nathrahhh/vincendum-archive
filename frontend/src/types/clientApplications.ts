export type ClientApplicationCreate = {
  name: string;
  industry: string;
  credit_limit: number;
};

export type ClientApplicationRecord = {
  id: number;
  name: string;
  industry: string;
  credit_limit: number;
  status: string;
};

export type ClientApplicationCreateResponse = {
  message: string;
  application?: ClientApplicationRecord;
  reasons?: string[];
};
