const mockEvaluations = [
  {
    name: "Zeta Healthcare Bridge",
    value: 1_500_000,
    industry: "Healthcare",
    status: "APPROVED",
  },
  {
    name: "Omega Tech Growth",
    value: 4_200_000,
    industry: "Technology",
    status: "REJECTED",
  },
  {
    name: "Sigma Retail Expansion",
    value: 900_000,
    industry: "Retail",
    status: "WARNING",
  },
  {
    name: "Lambda Energy Project",
    value: 2_100_000,
    industry: "Energy",
    status: "APPROVED",
  },
  {
    name: "Theta Manufacturing Facility",
    value: 3_500_000,
    industry: "Manufacturing",
    status: "REJECTED",
  },
];

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

export default function EvaluationsTable() {
  return (
    <section className="dashboard-panel">
      <p className="dashboard-panel__subtitle">Static mock data — API not available yet</p>
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
            {mockEvaluations.map((row) => (
              <tr key={row.name}>
                <td>{row.name}</td>
                <td className="dashboard-table__num">{formatValue(row.value)}</td>
                <td>{row.industry}</td>
                <td>
                  <span className={statusClass[row.status]}>{row.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
