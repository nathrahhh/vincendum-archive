/** Open Banking / bank transaction types (client-facing API). */

export type OpenBankingConnectionStart = {
  bank_connection_id: number;
  truelayer_connection_id: string;
  status: string;
  authorization_url: string | null;
};

export type BankAccount = {
  id: number;
  bank_connection_id: number;
  truelayer_account_id: string;
  account_type: string | null;
  currency: string | null;
  created_at: string;
  updated_at: string;
};

export type BankTransaction = {
  id: number;
  bank_account_id: number;
  truelayer_transaction_id: string;
  booking_date: string | null;
  value_date: string | null;
  amount: string | number;
  currency: string;
  description: string | null;
  transaction_type: string | null;
  created_at: string;
  updated_at: string;
};
