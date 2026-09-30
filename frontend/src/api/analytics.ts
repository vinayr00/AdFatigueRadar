export interface AnalyticsOverview {
  impressions: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  clicks: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  conversions: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  cpa: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  cpm: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  ctr: { value: number; change: number; is_positive: boolean; sparkline: number[] };
  performance_trend: Array<{
    date: string;
    impressions: number;
    clicks: number;
    conversions: number;
    cpa: number;
    cpm: number;
    risk_score: number;
  }>;
  sentiment_overview: {
    total_comments: number;
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
    spam_pct: number;
    sentiment_decay: number;
    fatigue_mockery: number;
    comment_acceleration: number;
  };
  risk_analysis: {
    audience_risk: number;
    economic_risk: number;
    state: "WATCH" | "WARNING" | "SOFT" | "CRITICAL";
    description: string;
    thresholds: { watch: number; warning: number; soft: number; critical: number };
  };
  platform_performance: Array<{
    platform: "meta" | "google" | "tiktok" | "youtube" | "x";
    name: string;
    impressions: number;
    change_pct: number;
    is_increase: boolean;
    color: string;
  }>;
  audience_insights: {
    age_groups: Array<{ group: string; percentage: number }>;
    gender: { male: number; female: number; other: number };
  };
}

export async function fetchAnalyticsData(filters?: Record<string, string>): Promise<AnalyticsOverview> {
  try {
    const res = await fetch(`/api/analytics?${new URLSearchParams(filters).toString()}`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }

  // Realistic mock analytics matching Analytics.png
  const trendData = [];
  const baseDate = new Date("2024-06-01");
  for (let i = 0; i < 30; i++) {
    const d = new Date(baseDate.getTime() + i * 24 * 3600 * 1000);
    const dateStr = `Jun ${d.getDate()}`;
    const imp = Math.round(180000 + Math.sin(i / 4) * 120000 + i * 11000 + (Math.random() * 40000 - 20000));
    const conv = Math.round(120 + Math.cos(i / 5) * 80 + i * 4.5 + (Math.random() * 30 - 15));
    const risk = Number((0.15 + (i / 30) * 0.55 + Math.sin(i / 3) * 0.05).toFixed(2));
    trendData.push({
      date: dateStr,
      impressions: imp,
      clicks: Math.round(imp * 0.017),
      conversions: conv,
      cpa: Number((imp * 0.009 / Math.max(1, conv)).toFixed(2)),
      cpm: 7.80,
      risk_score: risk,
    });
  }

  return {
    impressions: { value: 8400000, change: 18, is_positive: true, sparkline: [7.2, 7.5, 7.8, 8.0, 8.2, 8.4] },
    clicks: { value: 142300, change: -12, is_positive: false, sparkline: [160, 155, 150, 145, 142.3] },
    conversions: { value: 3600, change: -28, is_positive: false, sparkline: [5.0, 4.6, 4.2, 3.9, 3.6] },
    cpa: { value: 16.40, change: 35, is_positive: false, sparkline: [12.1, 13.4, 14.8, 15.6, 16.4] },
    cpm: { value: 7.80, change: 22, is_positive: false, sparkline: [6.4, 6.8, 7.2, 7.5, 7.8] },
    ctr: { value: 1.7, change: -18, is_positive: false, sparkline: [2.1, 1.9, 1.8, 1.75, 1.7] },
    performance_trend: trendData,
    sentiment_overview: {
      total_comments: 312000,
      positive_pct: 42,
      neutral_pct: 28,
      negative_pct: 24,
      spam_pct: 6,
      sentiment_decay: 0.61,
      fatigue_mockery: 0.55,
      comment_acceleration: 0.42,
    },
    risk_analysis: {
      audience_risk: 0.68,
      economic_risk: 0.52,
      state: "WARNING",
      description: "Audience fatigue risk is elevated. Negative sentiment and comment volume are increasing.",
      thresholds: { watch: 0.50, warning: 0.65, soft: 0.75, critical: 0.85 },
    },
    platform_performance: [
      { platform: "meta", name: "Meta Ads", impressions: 3200000, change_pct: 12, is_increase: true, color: "#1877F2" },
      { platform: "google", name: "Google Ads", impressions: 2400000, change_pct: 8, is_increase: true, color: "#EA4335" },
      { platform: "tiktok", name: "TikTok Ads", impressions: 1600000, change_pct: -16, is_increase: false, color: "#000000" },
      { platform: "youtube", name: "YouTube Ads", impressions: 820000, change_pct: 22, is_increase: true, color: "#FF0000" },
      { platform: "x", name: "X (Twitter) Ads", impressions: 410000, change_pct: -8, is_increase: false, color: "#1DA1F2" },
    ],
    audience_insights: {
      age_groups: [
        { group: "13-17", percentage: 12 },
        { group: "18-24", percentage: 28 },
        { group: "25-34", percentage: 32 },
        { group: "35-44", percentage: 18 },
        { group: "45-54", percentage: 8 },
        { group: "55+", percentage: 2 },
      ],
      gender: { male: 62, female: 36, other: 2 },
    },
  };
}
