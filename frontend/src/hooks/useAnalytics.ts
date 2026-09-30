import { useQuery } from "@tanstack/react-query";
import { fetchAnalyticsData } from "../api/analytics";

export function useAnalytics(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ["analytics", filters],
    queryFn: () => fetchAnalyticsData(filters),
    staleTime: 30000,
  });
}
