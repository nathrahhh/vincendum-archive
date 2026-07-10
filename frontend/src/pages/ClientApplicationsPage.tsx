import { useCallback, useEffect, useState } from "react";
import {
  approveClientApplication,
  fetchClientApplications,
  rejectClientApplication,
} from "../services/clientApplicationService";
import type { ClientApplicationRecord } from "../types";

const statusClass: Record<string, string> = {
  pending: "dashboard-badge dashboard-badge--warning",
  approved: "dashboard-badge dashboard-badge--approved",
  rejected: "dashboard-badge dashboard-badge--rejected",
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value: string | undefined): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ClientApplicationsPage() {
  const [applications, setApplications] = useState<ClientApplicationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  const loadApplications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchClientApplications();
      setApplications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load client applications");
      setApplications([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  async function handleApprove(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await approveClientApplication(id);
      await loadApplications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve application");
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleReject(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await rejectClientApplication(id);
      await loadApplications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject application");
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        {error ? <p className="dashboard-error">{error}</p> : null}
        {isLoading ? (
          <p className="dashboard-panel__subtitle">Loading client applications…</p>
        ) : null}
        {!isLoading && !error && applications.length === 0 ? (
          <p className="dashboard-panel__subtitle">No client applications yet.</p>
        ) : null}
        {!isLoading && applications.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Industry</th>
                  <th>Credit Limit</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((application) => (
                  <tr key={application.id}>
                    <td>{application.name}</td>
                    <td>{application.industry}</td>
                    <td className="dashboard-table__num">
                      {formatCurrency(application.credit_limit)}
                    </td>
                    <td>
                      <span
                        className={
                          statusClass[application.status] ?? "dashboard-badge"
                        }
                      >
                        {application.status}
                      </span>
                    </td>
                    <td>{formatDate(application.created_at)}</td>
                    <td>
                      {application.status === "pending" ? (
                        <>
                          <button
                            type="button"
                            disabled={actionLoadingId === application.id}
                            onClick={() => handleApprove(application.id)}
                          >
                            Approve
                          </button>{" "}
                          <button
                            type="button"
                            disabled={actionLoadingId === application.id}
                            onClick={() => handleReject(application.id)}
                          >
                            Reject
                          </button>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
