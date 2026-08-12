import { useCallback, useEffect, useState } from "react";
import { approveDeal, getDeals, rejectDeal } from "../services/dealService";
import type { DealRecord } from "../types";

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

export default function EvaluationsPage() {
  const [deals, setDeals] = useState<DealRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  const loadDeals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDeals();
      setDeals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deals");
      setDeals([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  async function handleApprove(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await approveDeal(id);
      await loadDeals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve deal");
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleReject(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await rejectDeal(id);
      await loadDeals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject deal");
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        {error ? <p className="dashboard-error">{error}</p> : null}
        {isLoading ? <p className="dashboard-panel__subtitle">Loading evaluations…</p> : null}
        {!isLoading && !error && deals.length === 0 ? (
          <p className="dashboard-panel__subtitle">No evaluated deals yet.</p>
        ) : null}
        {!isLoading && deals.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Value</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.name}</td>
                    <td className="dashboard-table__num">{formatValue(deal.value)}</td>
                    <td>
                      <span className={statusClass[deal.status ?? ""] ?? "dashboard-badge"}>
                        {deal.status ?? "—"}
                      </span>
                    </td>
                    <td>
                      {deal.status === "PENDING" ? (
                        <>
                          <button
                            type="button"
                            disabled={actionLoadingId === deal.id}
                            onClick={() => handleApprove(deal.id)}
                          >
                            Approve
                          </button>{" "}
                          <button
                            type="button"
                            disabled={actionLoadingId === deal.id}
                            onClick={() => handleReject(deal.id)}
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
