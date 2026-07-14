import type { Client, ClientFinancials, ClientForecast } from "../../types";
import CashBalanceChart from "./CashBalanceChart";
import RevenueGrossProfitChart from "./RevenueGrossProfitChart";

type ClientDetailPanelProps = {
  client: Client | null;
  financials: ClientFinancials | null;
  forecast: ClientForecast | null;
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

  const deals = client.deals ?? [];

  return (
    <aside className="clients-panel">
      <h2 className="clients-panel__title">{client.name}</h2>
      <p className="clients-panel__meta">Industry: {client.industry}</p>
      <p className="clients-panel__meta">Credit limit: {formatCurrency(client.credit_limit)}</p>

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

      {!isLoading ? (
        <>
          <section>
            <h3 className="deal-result-panel__breaches-title">Cash Balance</h3>
            <CashBalanceChart financials={financials} forecast={forecast} />
          </section>
          <section>
            <h3 className="deal-result-panel__breaches-title">Revenue & Gross Profit</h3>
            <RevenueGrossProfitChart forecast={forecast} />
          </section>
        </>
      ) : null}
    </aside>
  );
}
