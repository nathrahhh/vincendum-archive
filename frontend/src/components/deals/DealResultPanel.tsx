import type { RiskEvaluation } from "../../types";

type DealResultPanelProps = {
  result: RiskEvaluation | null;
  error: string | null;
  isLoading: boolean;
};

const statusClass: Record<string, string> = {
  APPROVED: "dashboard-badge dashboard-badge--approved",
  WARNING: "dashboard-badge dashboard-badge--warning",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

export default function DealResultPanel({ result, error, isLoading }: DealResultPanelProps) {
  return (
    <aside className="deal-result-panel">
      <h2 className="deal-result-panel__title">Evaluation Result</h2>

      {isLoading ? <p className="deal-result-panel__hint">Evaluating deal…</p> : null}

      {error ? <p className="dashboard-error">{error}</p> : null}

      {!isLoading && !error && !result ? (
        <div className="deal-result-panel__empty">
          <p>No evaluation yet.</p>
          <p className="deal-result-panel__hint">Results will appear here after a deal is evaluated.</p>
        </div>
      ) : null}

      {result ? (
        <div className="deal-result-panel__content">
          <p>
            Status:{" "}
            <span className={statusClass[result.status] ?? "dashboard-badge"}>{result.status}</span>
          </p>
          <p className="deal-result-panel__meta">
            Portfolio value: {result.portfolio_value.toLocaleString()} · Utilisation:{" "}
            {result.capital_utilization_pct.toFixed(2)}%
          </p>

          {result.breaches.length > 0 ? (
            <div className="deal-result-panel__breaches">
              <h3 className="deal-result-panel__breaches-title">Breaches</h3>
              <ul className="deal-result-panel__breach-list">
                {result.breaches.map((breach, index) => (
                  <li key={`${breach.rule}-${index}`}>
                    <strong>{breach.rule}</strong> — {breach.detail}
                    <br />
                    <span className="deal-result-panel__hint">
                      Limit: {breach.limit_pct} · Actual: {breach.actual_pct}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="deal-result-panel__hint">No breaches.</p>
          )}
        </div>
      ) : null}
    </aside>
  );
}
