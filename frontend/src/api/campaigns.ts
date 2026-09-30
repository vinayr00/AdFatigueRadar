import { devRepository } from "../dev/repository";
import { Campaign, CampaignState } from "../types/contracts";

export async function fetchCampaigns(filters?: { status?: string; platform?: string; search?: string }): Promise<Campaign[]> {
  try {
    const res = await fetch(`/api/campaigns${filters ? `?status=${filters.status || ""}&platform=${filters.platform || ""}&search=${filters.search || ""}` : ""}`);
    if (res.ok) return await res.json();
  } catch {
    // Fallback to isolated dev repository
  }
  return devRepository.getCampaigns(filters);
}

export async function fetchCampaignById(id: string): Promise<Campaign | null> {
  try {
    const res = await fetch(`/api/campaigns/${id}`);
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return devRepository.getCampaignById(id);
}

export async function createCampaignApi(data: Partial<Campaign>): Promise<Campaign> {
  try {
    const res = await fetch(`/api/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return devRepository.createCampaign(data);
}

export async function pauseCampaignApi(campaignId: string): Promise<{ success: boolean; new_state: CampaignState; readback_verified: boolean }> {
  try {
    const res = await fetch(`/api/campaigns/${campaignId}/pause`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return devRepository.pauseCampaign(campaignId);
}

export async function unpauseCampaignApi(campaignId: string): Promise<{ success: boolean; new_state: CampaignState; readback_verified: boolean }> {
  try {
    const res = await fetch(`/api/campaigns/${campaignId}/unpause`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return devRepository.unpauseCampaign(campaignId);
}
