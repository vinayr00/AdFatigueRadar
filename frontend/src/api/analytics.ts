import { apiFetch } from "./client";
export interface AnalyticsOverview {
  impressions: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  clicks: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  conversions: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  cpa: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  cpm: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  ctr: { value: number | null; change: number; is_positive: boolean; sparkline: number[] };
  performance_trend: Array<{ date: string; impressions: number; clicks: number; conversions: number; cpa: number | null; cpm: number | null; risk_score: number }>;
  sentiment_overview: { total_comments: number; positive_pct: number | null; neutral_pct: number | null; negative_pct: number | null; spam_pct: number | null; sentiment_decay: number | null; fatigue_mockery: number | null; comment_acceleration: number | null };
  risk_analysis: { audience_risk: number; economic_risk: number | null; state: string; description: string; thresholds: { watch?: number; warning?: number; soft?: number; critical?: number } };
  platform_performance: Array<{ platform: "meta" | "google" | "tiktok" | "youtube" | "x"; name: string; impressions: number; change_pct: number | null; is_increase: boolean | null; color: string }>;
  audience_insights: { age_groups: Array<{ group: string; percentage: number }>; gender: { male: number | null; female: number | null; other: number | null } };
}
export function fetchAnalyticsData(filters?: Record<string, string>): Promise<AnalyticsOverview> {
  const query = new URLSearchParams(filters || {});
  return apiFetch(`/api/analytics${query.size ? `?${query}` : ""}`);
}
