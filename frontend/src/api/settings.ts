import { devRepository } from "../dev/repository";
import { SettingsData } from "../types/contracts";

export async function fetchSettings(): Promise<SettingsData> {
  try {
    const res = await fetch(`/api/settings`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return devRepository.getSettings();
}

export async function updateSettingsApi(settings: Partial<SettingsData>): Promise<SettingsData> {
  try {
    const res = await fetch(`/api/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return { ...devRepository.getSettings(), ...settings };
}
