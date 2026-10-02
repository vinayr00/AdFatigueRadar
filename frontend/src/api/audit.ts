import { AuditEvent } from "../types/contracts";
import { apiFetch } from "./client";

export function fetchAuditLogs(filters?: { search?: string; eventType?: string; user?: string; campaign?: string; severity?: string }): Promise<AuditEvent[]> {
  const params = new URLSearchParams();
  if (filters?.search) params.set("search", filters.search);
  if (filters?.eventType) params.set("event_type", filters.eventType);
  if (filters?.user) params.set("user", filters.user);
  if (filters?.campaign) params.set("campaign", filters.campaign);
  if (filters?.severity) params.set("severity", filters.severity);
  return apiFetch(`/api/audit-logs${params.size ? `?${params}` : ""}`);
}
