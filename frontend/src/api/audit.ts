import { devRepository } from "../dev/repository";
import { AuditEvent } from "../types/contracts";

export async function fetchAuditLogs(filters?: {
  search?: string;
  eventType?: string;
  user?: string;
  campaign?: string;
  severity?: string;
}): Promise<AuditEvent[]> {
  try {
    const params = new URLSearchParams();
    if (filters?.search) params.append("search", filters.search);
    if (filters?.eventType) params.append("event_type", filters.eventType);
    if (filters?.user) params.append("user", filters.user);
    if (filters?.campaign) params.append("campaign", filters.campaign);
    if (filters?.severity) params.append("severity", filters.severity);

    const res = await fetch(`/api/audit-logs?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }

  let list = devRepository.getAuditEvents();
  if (filters?.search) {
    const q = filters.search.toLowerCase();
    list = list.filter((e) => e.description.toLowerCase().includes(q) || e.user_name.toLowerCase().includes(q) || e.campaign_name.toLowerCase().includes(q));
  }
  if (filters?.eventType && filters.eventType !== "all" && filters.eventType !== "All Event Types") {
    list = list.filter((e) => e.event_type.toLowerCase() === filters.eventType?.toLowerCase());
  }
  if (filters?.severity && filters.severity !== "all" && filters.severity !== "All Severities") {
    list = list.filter((e) => e.severity.toLowerCase() === filters.severity?.toLowerCase());
  }
  if (filters?.campaign && filters.campaign !== "all" && filters.campaign !== "All Campaigns") {
    list = list.filter((e) => e.campaign_name.toLowerCase() === filters.campaign?.toLowerCase() || e.campaign_id === filters.campaign);
  }
  if (filters?.user && filters.user !== "all" && filters.user !== "All Users") {
    list = list.filter((e) => e.user_name.toLowerCase() === filters.user?.toLowerCase());
  }
  return list;
}
