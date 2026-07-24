import type { ClientDeal } from "../../types";

type ClientDealsTabProps = {
  deals: ClientDeal[];
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

export default function ClientDealsTab({ deals }: ClientDealsTabProps) {
  return (
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

                  <td className="dashboard-table__num">
                    {formatCurrency(deal.value)}
                  </td>

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
  );
}
