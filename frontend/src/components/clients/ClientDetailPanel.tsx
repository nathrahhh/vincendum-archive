import type { Client, ClientFinancials, ClientForecast } from "../../types";
import CashBalanceChart from "./CashBalanceChart";

type ClientDetailPanelProps = {
  client: Client | null;
  financials: ClientFinancials | null;
  forecast: ClientForecast | null;
  isLoading: boolean;
  error: string | null;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ClientDetailPanel({
  client,
  financials,
  forecast,
  isLoading,
  error,
}: ClientDetailPanelProps) {
  if (!client) {
    return (
      <aside className="clients-panel">
        <p className="clients-panel__hint">Select a client to view details.</p>
      </aside>
    );
  }

  return (
    <aside className="clients-panel">
      <h2 className="clients-panel__title">{client.name}</h2>
      <p className="clients-panel__meta">Industry: {client.industry}</p>
      <p className="clients-panel__meta">Credit limit: {formatCurrency(client.credit_limit)}</p>

      {error ? <p className="dashboard-error">{error}</p> : null}
      {isLoading ? <p className="clients-panel__hint">Loading client data…</p> : null}

      {!isLoading ? <CashBalanceChart financials={financials} forecast={forecast} /> : null}
    </aside>
  );
}
