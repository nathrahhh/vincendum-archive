import { useCallback, useEffect, useState } from "react";
import {
  approveClientFinancial,
  getClientFinancials,
  getClients,
  rejectClientFinancial,
} from "../services/clientService";
import type { ClientFinancialRecord } from "../types";

const statusClass: Record<string, string> = {
  PENDING: "dashboard-badge dashboard-badge--warning",
  APPROVED: "dashboard-badge dashboard-badge--approved",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

function formatValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMonth(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
  });
}

export default function FinancialEvaluationsPage() {
  const [submissions, setSubmissions] = useState<ClientFinancialRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  const loadSubmissions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const clients = await getClients();
      const financialBatches = await Promise.all(
        clients.map((client) => getClientFinancials(client.id)),
      );
      const records = financialBatches.flatMap((batch) => batch.historical);
      records.sort((a, b) => {
        const pendingRank = (status: string) => (status === "PENDING" ? 0 : 1);
        const byStatus = pendingRank(a.status) - pendingRank(b.status);
        if (byStatus !== 0) {
          return byStatus;
        }
        return b.id - a.id;
      });
      setSubmissions(records);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load client financial submissions",
      );
      setSubmissions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSubmissions();
  }, [loadSubmissions]);

  async function handleApprove(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await approveClientFinancial(id);
      await loadSubmissions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to approve client financial submission",
      );
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleReject(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await rejectClientFinancial(id);
      await loadSubmissions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reject client financial submission",
      );
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        {error ? <p className="dashboard-error">{error}</p> : null}
        {isLoading ? (
          <p className="dashboard-panel__subtitle">
            Loading financial submissions…
          </p>
        ) : null}
        {!isLoading && !error && submissions.length === 0 ? (
          <p className="dashboard-panel__subtitle">
            No client financial submissions yet.
          </p>
        ) : null}
        {!isLoading && submissions.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Client ID</th>
                  <th>Month</th>
                  <th>Revenue</th>
                  <th>COGS</th>
                  <th>Gross Profit</th>
                  <th>OPEX</th>
                  <th>Cash Balance</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.client_id}</td>
                    <td>{formatMonth(row.month)}</td>
                    <td className="dashboard-table__num">
                      {formatValue(row.revenue)}
                    </td>
                    <td className="dashboard-table__num">
                      {formatValue(row.cogs)}
                    </td>
                    <td className="dashboard-table__num">
                      {formatValue(row.gross_profit)}
                    </td>
                    <td className="dashboard-table__num">
                      {formatValue(row.opex)}
                    </td>
                    <td className="dashboard-table__num">
                      {formatValue(row.cash_balance)}
                    </td>
                    <td>
                      <span
                        className={
                          statusClass[row.status] ?? "dashboard-badge"
                        }
                      >
                        {row.status}
                      </span>
                    </td>
                    <td>
                      {row.status === "PENDING" ? (
                        <>
                          <button
                            type="button"
                            disabled={actionLoadingId === row.id}
                            onClick={() => handleApprove(row.id)}
                          >
                            Approve
                          </button>{" "}
                          <button
                            type="button"
                            disabled={actionLoadingId === row.id}
                            onClick={() => handleReject(row.id)}
                          >
                            Reject
                          </button>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
