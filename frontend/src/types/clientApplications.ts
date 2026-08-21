export type ClientApplicationRecord = {
  id: number;
  lender_id: number;
  name: string;
  industry: string;
  credit_limit: number;
  registered_business_name: string | null;
  companies_house_number: string | null;
  incorporation_year: number | null;
  headcount: number | null;
  revenue_last_fy: number | null;
  status: string;
  created_at?: string;
};

export type ClientApplicationCreate = {
  name: string;
  industry: string;
  credit_limit: number;
  registered_business_name?: string;
  companies_house_number?: string;
  incorporation_year?: number;
  headcount?: number;
  revenue_last_fy?: number;
};

export type ClientApplicationCreateResponse = {
  message: string;
  application?: ClientApplicationRecord;
};

export type ClientApplicationApproveResponse = {
  message: string;
  client: {
    id: number;
    name: string;
    industry: string;
    credit_limit: number;
  };
  application?: ClientApplicationRecord;
};

export type ClientApplicationRejectResponse = {
  message: string;
  application: ClientApplicationRecord;
};

export type DocumentRecord = {
  id: number;
  lender_id: number;
  client_id: number | null;
  application_id: number | null;
  name: string;
  storage_type: string;
  storage_key: string | null;
  external_url: string | null;
  created_at?: string;
};

export type ApplicationDocumentUploadResponse = {
  document: DocumentRecord;
  upload_url: string;
};

export type ClientDocumentDownloadResponse = {
  document: DocumentRecord;
  download_url: string | null;
};
