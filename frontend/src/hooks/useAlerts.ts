import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, fetchRecommendedActions, fetchAutomationRules, toggleAutomationRuleApi, executeActionApi } from "../api/alerts";

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    staleTime: 15000,
  });
}

export function useRecommendedActions() {
  return useQuery({
    queryKey: ["recommended-actions"],
    queryFn: fetchRecommendedActions,
    staleTime: 15000,
  });
}

export function useAutomationRules() {
  return useQuery({
    queryKey: ["automation-rules"],
    queryFn: fetchAutomationRules,
    staleTime: 30000,
  });
}

export function useToggleAutomationRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) =>
      toggleAutomationRuleApi(ruleId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["automation-rules"] });
    },
  });
}

export function useExecuteAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ actionId, actionType }: { actionId: string; actionType: string }) =>
      executeActionApi(actionId, actionType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["recommended-actions"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
    },
  });
}
