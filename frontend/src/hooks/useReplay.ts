import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchReplaySnapshot, startReplayApi, resetReplayApi } from "../api/replay";

export function useReplay(campaignId: string = "cmp_summer_2024", speed: number = 1) {
  return useQuery({
    queryKey: ["replay", campaignId, speed],
    queryFn: () => fetchReplaySnapshot(campaignId, speed),
    staleTime: 1000,
    refetchInterval: 2000,
  });
}

export function useStartReplay() {
  return useMutation({
    mutationFn: ({ campaignId, speed }: { campaignId: string; speed: number }) =>
      startReplayApi(campaignId, speed),
  });
}

export function useResetReplay() {
  return useMutation({
    mutationFn: (campaignId: string) => resetReplayApi(campaignId),
  });
}
