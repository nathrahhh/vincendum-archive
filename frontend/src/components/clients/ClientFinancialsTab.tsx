import type { ClientFinancials } from "../../types";

type ClientFinancialsTabProps = {
  financials: ClientFinancials | null;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ClientFinancialsTab({
  financials,
}: ClientFinancialsTabProps) {
  return (
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
                  <td>{formatCurrency(record.revenue)}</td>
                  <td>{formatCurrency(record.cogs)}</td>
                  <td>{formatCurrency(record.gross_profit)}</td>
                  <td>{formatCurrency(record.opex)}</td>
                  <td>{formatCurrency(record.cash_balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
