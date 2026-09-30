export interface ComparisonMetrics {
  campaign_a: {
    id: string;
    name: string;
    platform: string;
    category: string;
    thumbnail: string;
    impressions: number;
    clicks: number;
    conversions: number;
    cpa: number;
    cpm: number;
    ctr: number;
    sentiment_decay: number;
    negative_ratio: number;
    comment_acceleration: number;
    ctr_frequency: number;
    critical_complaints: number;
    sentiment: { positive: number; neutral: number; negative: number };
  };
  campaign_b: {
    id: string;
    name: string;
    platform: string;
    category: string;
    thumbnail: string;
    impressions: number;
    clicks: number;
    conversions: number;
    cpa: number;
    cpm: number;
    ctr: number;
    sentiment_decay: number;
    negative_ratio: number;
    comment_acceleration: number;
    ctr_frequency: number;
    critical_complaints: number;
    sentiment: { positive: number; neutral: number; negative: number };
  };
  risk_timeline: Array<{
    date: string;
    risk_a: number;
    risk_b: number;
  }>;
  platform_breakdown: Array<{
    platform: string;
    impressions_a: number;
    impressions_b: number | null;
    diff_pct: number | null;
  }>;
  top_comment_categories: Array<{
    category: string;
    pct_a: number;
    pct_b: number;
  }>;
  insights: Array<{
    type: "positive" | "negative" | "warning";
    text: string;
  }>;
  winner_summary?: {
    winner_name: string;
    summary: string;
  };
}

export async function fetchComparisonData(campaignAId: string, campaignBId: string): Promise<ComparisonMetrics> {
  try {
    const res = await fetch(`/api/comparisons?campaign_a=${campaignAId}&campaign_b=${campaignBId}`);
    if (res.ok) return await res.json();
  } catch {
    // Dev fallback
  }

  const riskTimeline = [];
  const baseDate = new Date("2024-06-01");
  for (let i = 0; i < 30; i++) {
    const d = new Date(baseDate.getTime() + i * 24 * 3600 * 1000);
    const dateStr = `Jun ${d.getDate()}`;
    const riskA = Number((0.10 + (i / 30) * 0.65 + Math.sin(i / 2) * 0.04).toFixed(2));
    const riskB = Number((0.08 + (i / 30) * 0.32 + Math.cos(i / 3) * 0.03).toFixed(2));
    riskTimeline.push({ date: dateStr, risk_a: riskA, risk_b: riskB });
  }

  return {
    campaign_a: {
      id: campaignAId || "cmp_summer_2024",
      name: "Summer Collection 2024",
      platform: "meta",
      category: "Fashion",
      thumbnail: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=120&q=80",
      impressions: 1200000,
      clicks: 16800,
      conversions: 312,
      cpa: 18.40,
      cpm: 9.10,
      ctr: 1.4,
      sentiment_decay: 0.61,
      negative_ratio: 24,
      comment_acceleration: 0.42,
      ctr_frequency: 0.58,
      critical_complaints: 0.21,
      sentiment: { positive: 52, neutral: 28, negative: 20 },
    },
    campaign_b: {
      id: campaignBId || "cmp_monsoon_sale",
      name: "Monsoon Sale",
      platform: "google",
      category: "Fashion",
      thumbnail: "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=120&q=80",
      impressions: 850000,
      clicks: 12100,
      conversions: 210,
      cpa: 23.10,
      cpm: 12.50,
      ctr: 1.3,
      sentiment_decay: 0.42,
      negative_ratio: 16,
      comment_acceleration: 0.28,
      ctr_frequency: 0.46,
      critical_complaints: 0.11,
      sentiment: { positive: 62, neutral: 26, negative: 12 },
    },
    risk_timeline: riskTimeline,
    platform_breakdown: [
      { platform: "Meta Ads", impressions_a: 1200000, impressions_b: 420000, diff_pct: 186 },
      { platform: "Google Ads", impressions_a: 0, impressions_b: 850000, diff_pct: null },
      { platform: "TikTok Ads", impressions_a: 320000, impressions_b: 210000, diff_pct: 52 },
      { platform: "YouTube Ads", impressions_a: 180000, impressions_b: 120000, diff_pct: 50 },
      { platform: "X (Twitter) Ads", impressions_a: 95000, impressions_b: 60000, diff_pct: 58 },
    ],
    top_comment_categories: [
      { category: "Product Complaint", pct_a: 32, pct_b: 18 },
      { category: "Service Complaint", pct_a: 18, pct_b: 14 },
      { category: "Fatigue", pct_a: 24, pct_b: 16 },
      { category: "Mockery", pct_a: 14, pct_b: 8 },
      { category: "Spam", pct_a: 6, pct_b: 4 },
    ],
    insights: [
      { type: "positive", text: "Campaign A has 41% more impressions with 20% lower CPA." },
      { type: "positive", text: "Higher conversion rate (+0.6%) in Campaign A." },
      { type: "warning", text: "Audience fatigue risk is increasing faster in Campaign A after Jun 18." },
      { type: "negative", text: "Campaign B has better comment sentiment and lower negative mention ratio." },
    ],
    winner_summary: {
      winner_name: "Summer Collection 2024",
      summary: "Better performance with lower costs and higher engagement, but monitor fatigue risk closely.",
    },
  };
}
