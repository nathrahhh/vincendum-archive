import type { PortfolioSummary } from "../../types";

type PortfolioSummaryPanelProps = {
  summary: PortfolioSummary;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export default function PortfolioSummaryPanel({ summary }: PortfolioSummaryPanelProps) {
  return (
    <article className="dashboard-panel dashboard-portfolio-card">
      <h2 className="dashboard-panel__title">{summary.portfolio_name}</h2>
      <dl className="dashboard-summary">
        <div className="dashboard-summary__row">
          <dt>Capital allocation</dt>
          <dd>{formatCurrency(summary.capital_allocation)}</dd>
        </div>
        <div className="dashboard-summary__row">
          <dt>Total exposure</dt>
          <dd>{formatCurrency(summary.total_exposure)}</dd>
        </div>
        <div className="dashboard-summary__row">
          <dt>Utilisation</dt>
          <dd>{formatPercent(summary.utilization_pct)}</dd>
        </div>
        <div className="dashboard-summary__row">
          <dt>Positions</dt>
          <dd>{summary.position_count}</dd>
        </div>
        <div className="dashboard-summary__row">
          <dt>Clients</dt>
          <dd>{summary.client_count}</dd>
        </div>
      </dl>
    </article>
  );
}
