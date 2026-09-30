import { devRepository } from "../dev/repository";
import { ReplayState } from "../types/contracts";

export async function startReplayApi(campaignId: string, speed: number = 1): Promise<{ status: string; current_hour: number }> {
  try {
    const res = await fetch(`/campaigns/${campaignId}/replay/start?speed=${speed}`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return { status: "RUNNING", current_hour: 0 };
}

export async function resetReplayApi(campaignId: string): Promise<{ status: string; current_hour: number }> {
  try {
    const res = await fetch(`/campaigns/${campaignId}/replay/reset`, { method: "POST" });
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return { status: "RESET", current_hour: 0 };
}

export async function fetchReplaySnapshot(campaignId: string, speed: number = 1): Promise<ReplayState> {
  try {
    const res = await fetch(`/campaigns/${campaignId}/replay/snapshot`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return devRepository.getReplayData(campaignId, speed);
}
