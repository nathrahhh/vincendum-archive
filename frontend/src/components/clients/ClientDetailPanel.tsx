import { useEffect, useState } from "react";
import type { Client, ClientFinancials, ClientForecast } from "../../types";
import { updateClientCreditLimit } from "../../services/clientService";
import DeterministicForecastChart from "./DeterministicForecastChart";
import ProphetForecastChart from "./ProphetForecastChart";

type ClientDetailPanelProps = {
  client: Client | null;
  financials: ClientFinancials | null;
  forecast: ClientForecast | null;
  onClientUpdated: () => Promise<void> | void;
  isLoading: boolean;
  error: string | null;
};

const statusClass: Record<string, string> = {
  PENDING: "dashboard-badge dashboard-badge--warning",
  APPROVED: "dashboard-badge dashboard-badge--approved",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function ClientDetailPanel({
  client,
  financials,
  forecast,
  onClientUpdated,
  isLoading,
  error,
}: ClientDetailPanelProps) {
  const [draftCreditLimit, setDraftCreditLimit] = useState(client?.credit_limit ?? 0);
  const [isUpdatingCreditLimit, setIsUpdatingCreditLimit] = useState(false);
  const [creditLimitError, setCreditLimitError] = useState<string | null>(null);

  useEffect(() => {
    setDraftCreditLimit(client?.credit_limit ?? 0);
    setCreditLimitError(null);
  }, [client?.id, client?.credit_limit]);

  if (!client) {
    return (
      <aside className="clients-panel">
        <p className="clients-panel__hint">Select a client to view details.</p>
      </aside>
    );
  }

  const deals = client.deals ?? [];

  async function handleUpdateCreditLimit() {
    setIsUpdatingCreditLimit(true);
    setCreditLimitError(null);
    try {
      await updateClientCreditLimit(client.id, Number(draftCreditLimit));
      await onClientUpdated();
    } catch (err) {
      setCreditLimitError(
        err instanceof Error ? err.message : "Failed to update credit limit",
      );
    } finally {
      setIsUpdatingCreditLimit(false);
    }
  }

  return (
    <aside className="clients-panel">
      <h2 className="clients-panel__title">{client.name}</h2>
      <p className="clients-panel__meta">Industry: {client.industry}</p>

      <section>
        <h3 className="deal-result-panel__breaches-title">Credit limit</h3>
        <label className="deal-form__field">
          <span className="deal-form__label">Credit Limit (USD)</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={draftCreditLimit}
            onChange={(e) => setDraftCreditLimit(Number(e.target.value))}
          />
        </label>
        <button
          className="deal-form__submit"
          type="button"
          disabled={isUpdatingCreditLimit}
          onClick={handleUpdateCreditLimit}
        >
          {isUpdatingCreditLimit ? "Updating…" : "Update"}
        </button>
        {creditLimitError ? <p className="dashboard-error">{creditLimitError}</p> : null}
      </section>

      <section>
        <h3 className="deal-result-panel__breaches-title">Exposure</h3>
        <p className="clients-panel__meta">
          Current exposure: {formatCurrency(client.current_exposure ?? 0)}
        </p>
        <p className="clients-panel__meta">
          Remaining credit: {formatCurrency(client.remaining_credit ?? 0)}
        </p>
        <p className="clients-panel__meta">
          Utilization: {formatPercent(client.utilization_pct ?? 0)}
        </p>
      </section>

      <section>
        <h3 className="deal-result-panel__breaches-title">Deals</h3>
        {deals.length === 0 ? (
          <p className="clients-panel__hint">No approved deals for this client.</p>
        ) : (
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
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.name}</td>
                    <td className="dashboard-table__num">{formatCurrency(deal.value)}</td>
                    <td>{deal.industry}</td>
                    <td>
                      <span className={statusClass[deal.status] ?? "dashboard-badge"}>
                        {deal.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h3 className="deal-result-panel__breaches-title">Financial History</h3>
        {!financials || financials.historical.length === 0 ? (
          <p className="clients-panel__hint">No financial history for this client.</p>
        ) : (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Revenue</th>
                  <th>COGS</th>
                  <th>Gross Profit</th>
                  <th>Opex</th>
                  <th>Cash Balance</th>
                </tr>
              </thead>
              <tbody>
                {financials.historical.map((record) => (
                  <tr key={record.id}>
                    <td>{record.month.slice(0, 7)}</td>
                    <td className="dashboard-table__num">{formatCurrency(record.revenue)}</td>
                    <td className="dashboard-table__num">{formatCurrency(record.cogs)}</td>
                    <td className="dashboard-table__num">{formatCurrency(record.gross_profit)}</td>
                    <td className="dashboard-table__num">{formatCurrency(record.opex)}</td>
                    <td className="dashboard-table__num">{formatCurrency(record.cash_balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {error ? <p className="dashboard-error">{error}</p> : null}
      {isLoading ? <p className="clients-panel__hint">Loading client data…</p> : null}

      {!isLoading && forecast?.model_type === "prophet" ? (
        <section>
          <h3 className="deal-result-panel__breaches-title">Forecast</h3>
          <ProphetForecastChart
            historical={forecast.historical}
            forecast={forecast.forecast}
          />
        </section>
      ) : null}

      {!isLoading && forecast?.model_type === "deterministic" ? (
        <section>
          <h3 className="deal-result-panel__breaches-title">Forecast</h3>
          <DeterministicForecastChart
            historical={forecast.historical}
            forecast={forecast.forecast}
          />
        </section>
      ) : null}
    </aside>
  );
}
