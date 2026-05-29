import type { Position } from "../../types";

type PortfolioTableProps = {
  positions: Position[];
  isLoading?: boolean;
  error?: string | null;
};

function formatValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function PortfolioTable({ positions, isLoading, error }: PortfolioTableProps) {
  return (
    <section className="dashboard-panel">
      <h2 className="dashboard-panel__title">Portfolio</h2>
      {error ? <p className="dashboard-error">{error}</p> : null}
      {isLoading ? <p className="dashboard-panel__subtitle">Loading portfolio…</p> : null}
      {!isLoading && !error && positions.length === 0 ? (
        <p className="dashboard-panel__subtitle">No positions in portfolio.</p>
      ) : null}
      {!isLoading && positions.length > 0 ? (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Industry</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((row) => (
                <tr key={row.name}>
                  <td>{row.name}</td>
                  <td>{row.industry}</td>
                  <td className="dashboard-table__num">{formatValue(row.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
