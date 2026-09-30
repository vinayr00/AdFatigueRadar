import { useQuery } from "@tanstack/react-query";
import { fetchComparisonData } from "../api/comparisons";

export function useComparisons(campaignA: string, campaignB: string) {
  return useQuery({
    queryKey: ["comparisons", campaignA, campaignB],
    queryFn: () => fetchComparisonData(campaignA, campaignB),
    enabled: !!campaignA && !!campaignB,
    staleTime: 30000,
  });
}
