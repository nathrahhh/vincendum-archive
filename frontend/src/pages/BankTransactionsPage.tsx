import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  getOpenBankingAccounts,
  getOpenBankingTransactions,
  startOpenBankingConnect,
} from "../services/openBankingService";
import type { BankAccount, BankTransaction } from "../types/openBanking";

function formatAmount(amount: string | number, currency: string): string {
  const value = typeof amount === "number" ? amount : Number(amount);
  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: currency || "GBP",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency}`;
  }
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function amountClass(amount: string | number): string {
  const value = typeof amount === "number" ? amount : Number(amount);
  if (value > 0) {
    return "dashboard-table__num bank-tx__amount--credit";
  }
  if (value < 0) {
    return "dashboard-table__num bank-tx__amount--debit";
  }
  return "dashboard-table__num";
}

export default function BankTransactionsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);

  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadAccounts = useCallback(async () => {
    setIsLoadingAccounts(true);
    setError(null);
    try {
      const data = await getOpenBankingAccounts();
      setAccounts(data);
      setSelectedAccountId((current) => {
        if (current !== null && data.some((account) => account.id === current)) {
          return current;
        }
        return data[0]?.id ?? null;
      });
      if (data.length === 0) {
        setTransactions([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load accounts");
      setAccounts([]);
      setSelectedAccountId(null);
      setTransactions([]);
    } finally {
      setIsLoadingAccounts(false);
    }
  }, []);

  const loadTransactions = useCallback(async (accountId: number) => {
    setIsLoadingTransactions(true);
    setError(null);
    try {
      const data = await getOpenBankingTransactions(accountId);
      setTransactions(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load transactions";
      if (message.toLowerCase().includes("409") || message.includes("API 409")) {
        setError("Bank connection not authorised");
      } else {
        setError(message);
      }
      setTransactions([]);
    } finally {
      setIsLoadingTransactions(false);
    }
  }, []);

  useEffect(() => {
    const status = searchParams.get("status");
    if (status === "success") {
      setStatusMessage("Bank account connected successfully. Syncing accounts…");
      navigate("/client/bank-transactions", { replace: true });
    } else if (status === "failure") {
      setError("Bank connection was cancelled or failed. Please try again.");
      navigate("/client/bank-transactions", { replace: true });
    }
    // Handle callback query once on mount; do not re-run on param clear.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    if (selectedAccountId === null) {
      return;
    }
    void loadTransactions(selectedAccountId);
  }, [loadTransactions, selectedAccountId]);

  async function handleConnect() {
    setIsConnecting(true);
    setError(null);
    setStatusMessage(null);
    try {
      const result = await startOpenBankingConnect();
      if (!result.authorization_url) {
        setError("Failed to connect bank: no authorisation URL returned");
        return;
      }
      window.location.assign(result.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect bank");
      setIsConnecting(false);
    }
  }

  const selectedAccount =
    accounts.find((account) => account.id === selectedAccountId) ?? null;
  const hasConnectedAccounts = accounts.length > 0;

  return (
    <div className="bank-transactions-page">
      {error ? <p className="dashboard-error">{error}</p> : null}
      {statusMessage ? (
        <p className="client-financials__success">{statusMessage}</p>
      ) : null}

      {!isLoadingAccounts && !hasConnectedAccounts ? (
        <section className="dashboard-panel">
          <h2 className="dashboard-panel__title">Bank Transactions</h2>
          <p className="dashboard-panel__subtitle">
            Connect your business bank account to securely provide transaction
            data for financial monitoring.
          </p>
          <button
            type="button"
            className="deal-form__submit"
            onClick={handleConnect}
            disabled={isConnecting}
          >
            {isConnecting ? "Connecting…" : "Connect bank account"}
          </button>
        </section>
      ) : null}

      {isLoadingAccounts ? (
        <section className="dashboard-panel">
          <p className="dashboard-panel__subtitle">Loading accounts…</p>
        </section>
      ) : null}

      {!isLoadingAccounts && hasConnectedAccounts ? (
        <>
          <section className="dashboard-panel">
            <div className="bank-tx__header">
              <div>
                <h2 className="dashboard-panel__title">Bank Transactions</h2>
                <p className="dashboard-panel__subtitle">
                  Transaction visibility for financial monitoring.
                </p>
              </div>
              <button
                type="button"
                className="deal-form__submit"
                onClick={handleConnect}
                disabled={isConnecting}
              >
                {isConnecting ? "Connecting…" : "Connect another account"}
              </button>
            </div>

            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Account</th>
                    <th>Type</th>
                    <th>Currency</th>
                    <th>Status</th>
                    <th>Last sync</th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.map((account, index) => (
                    <tr
                      key={account.id}
                      className={
                        account.id === selectedAccountId
                          ? "bank-tx__account-row bank-tx__account-row--active"
                          : "bank-tx__account-row"
                      }
                      onClick={() => setSelectedAccountId(account.id)}
                    >
                      <td>Account {index + 1}</td>
                      <td>{account.account_type ?? "—"}</td>
                      <td>{account.currency ?? "—"}</td>
                      <td>
                        <span className="dashboard-badge dashboard-badge--approved">
                          Connected
                        </span>
                      </td>
                      <td>{formatDateTime(account.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="dashboard-panel bank-tx__transactions">
            <h3 className="dashboard-panel__title">
              Transactions
              {selectedAccount
                ? ` · Account ${accounts.findIndex((a) => a.id === selectedAccount.id) + 1}`
                : ""}
            </h3>

            {isLoadingTransactions ? (
              <p className="dashboard-panel__subtitle">Loading transactions…</p>
            ) : null}

            {!isLoadingTransactions && transactions.length === 0 ? (
              <p className="dashboard-panel__subtitle">
                No transactions found for this account in the current sync
                window.
              </p>
            ) : null}

            {!isLoadingTransactions && transactions.length > 0 ? (
              <div className="dashboard-table-wrap">
                <table className="dashboard-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Description</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Currency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((txn) => (
                      <tr key={txn.id}>
                        <td>{formatDate(txn.booking_date)}</td>
                        <td>{txn.description ?? "—"}</td>
                        <td>{txn.transaction_type ?? "—"}</td>
                        <td className={amountClass(txn.amount)}>
                          {formatAmount(txn.amount, txn.currency)}
                        </td>
                        <td>{txn.currency}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
