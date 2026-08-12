import { useEffect, useState } from "react";
import { getDeals } from "../../services/dealService";
import type { DealRecord } from "../../types";

const statusClass: Record<string, string> = {
  APPROVED: "dashboard-badge dashboard-badge--approved",
  WARNING: "dashboard-badge dashboard-badge--warning",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

function formatValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function RecentDeals() {
  const [deals, setDeals] = useState<DealRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDeals() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getDeals();
        if (!cancelled) {
          setDeals(data.slice(0, 5));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load deals");
          setDeals([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadDeals();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="dashboard-panel">
      <h2 className="dashboard-panel__title">Recent Deals</h2>
      {error ? <p className="dashboard-error">{error}</p> : null}
      {isLoading ? <p className="dashboard-panel__subtitle">Loading recent deals…</p> : null}
      {!isLoading && !error && deals.length === 0 ? (
        <p className="dashboard-panel__subtitle">No deals yet.</p>
      ) : null}
      {!isLoading && deals.length > 0 ? (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Deal</th>
                <th>Value</th>
                <th>Status</th>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
