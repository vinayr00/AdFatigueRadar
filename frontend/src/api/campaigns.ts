import { Campaign, CampaignState } from "../types/contracts";
import { apiFetch } from "./client";

export function fetchCampaigns(filters?: { status?: string; platform?: string; search?: string }): Promise<Campaign[]> {
  const query = new URLSearchParams();
  Object.entries(filters || {}).forEach(([key, value]) => value && query.set(key, value));
  return apiFetch(`/api/campaigns${query.size ? `?${query}` : ""}`);
}

export function fetchCampaignById(id: string): Promise<Campaign> {
  return apiFetch(`/api/campaigns/${encodeURIComponent(id)}`);
}

export function createCampaignApi(data: Partial<Campaign>): Promise<Campaign> {
  return apiFetch("/api/campaigns", { method: "POST", body: JSON.stringify(data) });
}

export function pauseCampaignApi(campaignId: string): Promise<{ success: boolean; new_state: CampaignState; readback_verified: boolean }> {
  return apiFetch(`/api/campaigns/${encodeURIComponent(campaignId)}/pause`, { method: "POST" });
}

export function unpauseCampaignApi(campaignId: string): Promise<{ success: boolean; new_state: CampaignState; readback_verified: boolean }> {
  return apiFetch(`/api/campaigns/${encodeURIComponent(campaignId)}/unpause`, { method: "POST" });
}

export function deleteCampaignApi(campaignId: string): Promise<{ success: boolean; campaign_id: string; message: string }> {
  return apiFetch(`/api/campaigns/${encodeURIComponent(campaignId)}`, { method: "DELETE" });
}
