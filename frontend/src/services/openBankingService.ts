import {
  fetchOpenBankingAccounts,
  fetchOpenBankingTransactions,
  postOpenBankingConnect,
} from "../api/openBanking";
import type {
  BankAccount,
  BankTransaction,
  OpenBankingConnectionStart,
} from "../types/openBanking";
import { toServiceError } from "./errors";

export async function startOpenBankingConnect(): Promise<OpenBankingConnectionStart> {
  try {
    return await postOpenBankingConnect();
  } catch (error) {
    throw toServiceError(error, "Failed to connect bank");
  }
}

export async function getOpenBankingAccounts(): Promise<BankAccount[]> {
  try {
    return await fetchOpenBankingAccounts();
  } catch (error) {
    throw toServiceError(error, "Failed to load accounts");
  }
}

export async function getOpenBankingTransactions(
  accountId: number,
): Promise<BankTransaction[]> {
  try {
    return await fetchOpenBankingTransactions(accountId);
  } catch (error) {
    throw toServiceError(error, "Failed to load transactions");
  }
}
