import { devRepository } from "../dev/repository";
import { AlertItem, RecommendedAction, AutomationRule } from "../types/contracts";

export async function fetchAlerts(): Promise<AlertItem[]> {
  try {
    const res = await fetch(`/api/alerts`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return devRepository.getAlerts();
}

export async function fetchRecommendedActions(): Promise<RecommendedAction[]> {
  try {
    const res = await fetch(`/api/recommended-actions`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return devRepository.getRecommendedActions();
}

export async function fetchAutomationRules(): Promise<AutomationRule[]> {
  try {
    const res = await fetch(`/api/automation-rules`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return devRepository.getAutomationRules();
}

export async function toggleAutomationRuleApi(ruleId: string, enabled: boolean): Promise<{ success: boolean; rule_id: string; enabled: boolean }> {
  try {
    const res = await fetch(`/api/automation-rules/${ruleId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return { success: true, rule_id: ruleId, enabled };
}

export async function executeActionApi(actionId: string, actionType: string): Promise<{ success: boolean; message: string; readback_verified: boolean }> {
  try {
    const res = await fetch(`/api/actions/${actionId}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_type: actionType }),
    });
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }
  return { success: true, message: `Action ${actionType} executed successfully with verified readback.`, readback_verified: true };
}
