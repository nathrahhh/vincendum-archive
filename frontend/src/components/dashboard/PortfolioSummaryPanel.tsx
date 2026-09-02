import { useEffect, useState, type FormEvent } from "react";
import type { PortfolioSummary, PortfolioUpdateRequest } from "../../types";

type PortfolioSummaryPanelProps = {
  summary: PortfolioSummary;
  onUpdate: (
    portfolioId: number,
    payload: PortfolioUpdateRequest,
  ) => Promise<void>;
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

export default function PortfolioSummaryPanel({
  summary,
  onUpdate,
}: PortfolioSummaryPanelProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(summary.portfolio_name);
  const [allocation, setAllocation] = useState(String(summary.capital_allocation));
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isEditing) {
      setName(summary.portfolio_name);
      setAllocation(String(summary.capital_allocation));
    }
  }, [summary, isEditing]);

  function handleModifyClick() {
    setError(null);
    setName(summary.portfolio_name);
    setAllocation(String(summary.capital_allocation));
    setIsEditing(true);
  }

  function handleCancelEdit() {
    setError(null);
    setName(summary.portfolio_name);
    setAllocation(String(summary.capital_allocation));
    setIsEditing(false);
  }

  async function handleSaveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onUpdate(summary.portfolio_id, {
        name: name.trim(),
        capital_allocation: Number(allocation),
      });
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update portfolio");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <article className="dashboard-panel dashboard-portfolio-card">
      <div className="dashboard-portfolio-card__header">
        <h2 className="dashboard-panel__title">{summary.portfolio_name}</h2>
        {!isEditing ? (
          <button
            type="button"
            className="dashboard-button dashboard-button--secondary"
            onClick={handleModifyClick}
          >
            Modify
          </button>
        ) : null}
      </div>

      {isEditing ? (
        <form className="dashboard-form" onSubmit={handleSaveEdit}>
          <label>
            Portfolio name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
          <label>
            Capital allocation
            <input
              type="number"
              min="0"
              step="any"
              value={allocation}
              onChange={(event) => setAllocation(event.target.value)}
              required
            />
          </label>
          {error ? <p className="dashboard-error">{error}</p> : null}
          <div className="dashboard-form__actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Save"}
            </button>
            <button
              type="button"
              className="dashboard-button dashboard-button--secondary"
              onClick={handleCancelEdit}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <dl className="dashboard-summary">
          <div className="dashboard-summary__row">
            <dt>Capital allocation</dt>
            <dd>{formatCurrency(summary.capital_allocation)}</dd>
          </div>
          <div className="dashboard-summary__row">
            <dt>Remaining capacity</dt>
            <dd>{formatCurrency(summary.remaining_capacity)}</dd>
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
      )}
    </article>
  );
}
