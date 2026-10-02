import { SettingsData } from "../types/contracts";
import { apiFetch } from "./client";

export const fetchSettings = (): Promise<SettingsData> => apiFetch("/api/settings");
export const updateSettingsApi = (settings: Partial<SettingsData>): Promise<SettingsData> =>
  apiFetch("/api/settings", { method: "PUT", body: JSON.stringify(settings) });
