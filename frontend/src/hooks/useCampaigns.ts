import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchCampaigns, fetchCampaignById, createCampaignApi, pauseCampaignApi, unpauseCampaignApi, deleteCampaignApi } from "../api/campaigns";
import { Campaign } from "../types/contracts";

export function useCampaigns(filters?: { status?: string; platform?: string; search?: string }) {
  return useQuery({
    queryKey: ["campaigns", filters],
    queryFn: () => fetchCampaigns(filters),
    staleTime: 30000,
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: ["campaign", id],
    queryFn: () => fetchCampaignById(id),
    enabled: !!id,
    staleTime: 1000,
    refetchInterval: 2000,
  });
}

export function useDemoCampaign(id: string) {
  return useQuery({
    queryKey: ["demo-campaign", id],
    queryFn: async () => {
      if (!id) return null;
      try {
        const res = await fetch(`/api/demo/campaigns/${encodeURIComponent(id)}`);
        if (!res.ok) return null;
        return await res.json();
      } catch {
        return null;
      }
    },
    enabled: !!id,
    staleTime: 500,
    refetchInterval: 1500,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Campaign>) => createCampaignApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function usePauseCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (campaignId: string) => pauseCampaignApi(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["campaign"] });
    },
  });
}

export function useUnpauseCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (campaignId: string) => unpauseCampaignApi(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["campaign"] });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (campaignId: string) => deleteCampaignApi(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["campaign"] });
    },
  });
}
