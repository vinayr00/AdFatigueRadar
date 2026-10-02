import { ReplayState } from "../types/contracts";
import { apiFetch } from "./client";

export function startReplayApi(campaignId: string, speed = 1): Promise<{ started: boolean; campaign_id: string; speed: number }> {
  return apiFetch(`/campaigns/${encodeURIComponent(campaignId)}/replay/start?speed=${encodeURIComponent(speed)}`, { method: "POST" });
}
export function resetReplayApi(campaignId: string): Promise<{ reset: boolean; campaign_id: string }> {
  return apiFetch(`/campaigns/${encodeURIComponent(campaignId)}/replay/reset`, { method: "POST" });
}
export const pauseReplayApi = (campaignId: string): Promise<{ paused: boolean; campaign_id: string }> =>
  apiFetch(`/campaigns/${encodeURIComponent(campaignId)}/replay/pause`, { method: "POST" });
export const resumeReplayApi = (campaignId: string): Promise<{ resumed: boolean; campaign_id: string }> =>
  apiFetch(`/campaigns/${encodeURIComponent(campaignId)}/replay/resume`, { method: "POST" });
export function fetchReplaySnapshot(campaignId: string, _speed = 1): Promise<ReplayState> {
  return apiFetch(`/api/replay/${encodeURIComponent(campaignId)}/snapshot`);
}
