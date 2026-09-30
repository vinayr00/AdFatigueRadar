import { useQuery } from "@tanstack/react-query";
import { fetchAuditLogs } from "../api/audit";

export function useAuditLog(filters?: {
  search?: string;
  eventType?: string;
  user?: string;
  campaign?: string;
  severity?: string;
}) {
  return useQuery({
    queryKey: ["audit-logs", filters],
    queryFn: () => fetchAuditLogs(filters),
    staleTime: 15000,
  });
}
