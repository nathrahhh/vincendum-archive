import type { DealRecord } from "../../types";

type EvaluationsTableProps = {
  deals: DealRecord[];
  isLoading?: boolean;
  error?: string | null;
};

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

export default function EvaluationsTable({ deals, isLoading, error }: EvaluationsTableProps) {
  return (
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
                <th>Industry</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((row) => (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td className="dashboard-table__num">{formatValue(row.value)}</td>
                  <td>{row.industry}</td>
                  <td>
                    <span className={statusClass[row.status ?? ""] ?? "dashboard-badge"}>
                      {row.status ?? "—"}
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
