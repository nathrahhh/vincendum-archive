import { useCallback, useEffect, useState } from "react";
import { getAuditLogs } from "../services/auditLogService";
import type { AuditLogRecord } from "../types/auditLogs";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function hasJsonContent(value: Record<string, unknown> | null): boolean {
  return value != null && Object.keys(value).length > 0;
}

function formatDetails(log: AuditLogRecord): string {
  const hasChanges = hasJsonContent(log.changes);
  const hasMetadata = hasJsonContent(log.metadata);

  if (!hasChanges && !hasMetadata) {
    return "—";
  }

  const payload: Record<string, unknown> = {};
  if (hasChanges) {
    payload.changes = log.changes;
  }
  if (hasMetadata) {
    payload.metadata = log.metadata;
  }

  return JSON.stringify(payload);
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getAuditLogs();
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        {error ? <p className="dashboard-error">{error}</p> : null}
        {isLoading ? (
          <p className="dashboard-panel__subtitle">Loading audit logs…</p>
        ) : null}
        {!isLoading && !error && logs.length === 0 ? (
          <p className="dashboard-panel__subtitle">No audit logs yet.</p>
        ) : null}
        {!isLoading && logs.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Resource ID</th>
                  <th>User ID</th>
                  <th>Date/Time</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.action}</td>
                    <td>{log.resource_type}</td>
                    <td className="dashboard-table__num">{log.resource_id}</td>
                    <td className="dashboard-table__num">{log.user_id}</td>
                    <td>{formatDateTime(log.created_at)}</td>
                    <td>{formatDetails(log)}</td>
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
