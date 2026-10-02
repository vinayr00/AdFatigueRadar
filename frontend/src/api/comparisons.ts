import { apiFetch } from "./client";
export interface ComparisonMetrics {
  campaign_a: {
    id: string; name: string; platform: string; category: string; thumbnail: string;
    impressions: number; clicks: number; conversions: number; cpa: number | null;
    cpm: number | null; ctr: number | null; sentiment_decay: number | null;
    negative_ratio: number | null; comment_acceleration: number | null;
    ctr_frequency: number | null; critical_complaints: number;
    sentiment: { positive: number | null; neutral: number | null; negative: number | null };
  };
  campaign_b: ComparisonMetrics["campaign_a"];
  risk_timeline: Array<{ date: string; risk_a: number | null; risk_b: number | null }>;
  platform_breakdown: Array<{ platform: string; impressions_a: number; impressions_b: number | null; diff_pct: number | null }>;
  top_comment_categories: Array<{ category: string; pct_a: number | null; pct_b: number | null }>;
  insights: Array<{ type: "positive" | "negative" | "warning"; text: string }>;
  winner_summary?: { winner_name: string; summary: string };
}
export function fetchComparisonData(campaignAId: string, campaignBId: string): Promise<ComparisonMetrics> {
  const params = new URLSearchParams({ campaign_a: campaignAId, campaign_b: campaignBId });
  return apiFetch(`/api/comparisons?${params}`);
}
