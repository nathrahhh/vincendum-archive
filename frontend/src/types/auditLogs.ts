export type AuditLogRecord = {
  id: number;
  lender_id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: number;
  created_at: string;
  changes: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
};
