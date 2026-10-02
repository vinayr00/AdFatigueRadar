import { AlertItem, RecommendedAction, AutomationRule } from "../types/contracts";
import { apiFetch } from "./client";

export const fetchAlerts = (): Promise<AlertItem[]> => apiFetch("/api/alerts");
export const fetchRecommendedActions = (): Promise<RecommendedAction[]> => apiFetch("/api/recommended-actions");
export const fetchAutomationRules = (): Promise<AutomationRule[]> => apiFetch("/api/automation-rules");

export function toggleAutomationRuleApi(ruleId: string, enabled: boolean): Promise<{ success: boolean; rule_id: string; enabled: boolean }> {
  return apiFetch(`/api/automation-rules/${encodeURIComponent(ruleId)}`, { method: "PATCH", body: JSON.stringify({ enabled }) });
}

export function executeActionApi(actionId: string, actionType: string): Promise<{ success: boolean; message: string; readback_verified: boolean }> {
  return apiFetch(`/api/actions/${encodeURIComponent(actionId)}/execute`, { method: "POST", body: JSON.stringify({ action_type: actionType }) });
}
