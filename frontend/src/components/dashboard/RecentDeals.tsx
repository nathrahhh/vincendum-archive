const recentDeals = [
  {
    name: "Zeta Healthcare Bridge",
    industry: "Healthcare",
    value: "$1,500,000",
    status: "APPROVED",
    date: "2026-05-27",
  },
  {
    name: "Omega Tech Growth",
    industry: "Technology",
    value: "$4,200,000",
    status: "REJECTED",
    date: "2026-05-26",
  },
  {
    name: "Sigma Retail Expansion",
    industry: "Retail",
    value: "$900,000",
    status: "WARNING",
    date: "2026-05-25",
  },
  {
    name: "Lambda Energy Project",
    industry: "Energy",
    value: "$2,100,000",
    status: "APPROVED",
    date: "2026-05-24",
  },
];

const statusClass: Record<string, string> = {
  APPROVED: "dashboard-badge dashboard-badge--approved",
  WARNING: "dashboard-badge dashboard-badge--warning",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

export default function RecentDeals() {
  return (
    <section className="dashboard-panel">
      <h2 className="dashboard-panel__title">Recent Deals</h2>
      <p className="dashboard-panel__subtitle">Static mock data</p>
      <div className="dashboard-table-wrap">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Deal</th>
              <th>Industry</th>
              <th>Value</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {recentDeals.map((deal) => (
              <tr key={deal.name}>
                <td>{deal.name}</td>
                <td>{deal.industry}</td>
                <td className="dashboard-table__num">{deal.value}</td>
                <td>
                  <span className={statusClass[deal.status]}>{deal.status}</span>
                </td>
                <td>{deal.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
