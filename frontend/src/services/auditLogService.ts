import { request } from "../api/client";
import type { AuditLogRecord } from "../types/auditLogs";
import { toServiceError } from "./errors";

/** GET /audit-logs */
export async function getAuditLogs(limit = 100): Promise<AuditLogRecord[]> {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    return await request<AuditLogRecord[]>(`/audit-logs?${params.toString()}`);
  } catch (error) {
    throw toServiceError(error, "Failed to load audit logs");
  }
}
