import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchCampaigns, fetchCampaignById, createCampaignApi, pauseCampaignApi, unpauseCampaignApi } from "../api/campaigns";
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
    staleTime: 30000,
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
