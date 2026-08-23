import { request } from "./client";
import type {
  BankAccount,
  BankTransaction,
  OpenBankingConnectionStart,
} from "../types/openBanking";

/** POST /client/me/open-banking/connect */
export async function postOpenBankingConnect(): Promise<OpenBankingConnectionStart> {
  return request<OpenBankingConnectionStart>("/client/me/open-banking/connect", {
    method: "POST",
  });
}

/** GET /client/me/open-banking/accounts */
export async function fetchOpenBankingAccounts(): Promise<BankAccount[]> {
  return request<BankAccount[]>("/client/me/open-banking/accounts");
}

/** GET /client/me/open-banking/accounts/{account_id}/transactions */
export async function fetchOpenBankingTransactions(
  accountId: number,
): Promise<BankTransaction[]> {
  return request<BankTransaction[]>(
    `/client/me/open-banking/accounts/${accountId}/transactions`,
  );
}
