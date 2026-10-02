/**
 * Hardcoded, consistent, and bulletproof single-value dataset.
 * All amounts are strictly formatted in Indian Rupees (INR ₹) in the 1000 to 7000 range.
 */

export interface CampaignData {
  id: string;
  name: string;
  platform: "meta" | "tiktok" | "google";
  status: "ACTIVE" | "WARNING" | "CRITICAL" | "PAUSED";
  risk_score: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cpa: number;
  cpm: number;
  spend: number;
  roas: number;
  date_range: string;
  created_at: string;
  thumbnail_url: string;
  category: string;
  target_audience: string;
  last_7_days_trend: number[];
}

export const HARDCODED_CAMPAIGNS: CampaignData[] = [
  {
    id: "camp_meta_fatigue",
    name: "Summer Creator Campaign",
    platform: "meta",
    status: "CRITICAL",
    risk_score: 0.87,
    impressions: 66600,
    clicks: 1832,
    conversions: 143,
    ctr: 0.0275,
    cpa: 1450, // in 1000 - 7000 range
    cpm: 1120, // in 1000 - 7000 range
    spend: 5840, // in 1000 - 7000 range
    roas: 3.77,
    date_range: "Jun 15 - Jul 15, 2026",
    created_at: "2026-09-17T10:00:00+05:30",
    thumbnail_url: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
    category: "Summer Apparel",
    target_audience: "18-34 Fashion Shoppers",
    last_7_days_trend: [120, 140, 160, 200, 280, 420, 680],
  },
  {
    id: "camp_meta_healthy",
    name: "Product Launch Campaign",
    platform: "meta",
    status: "ACTIVE",
    risk_score: 0.12,
    impressions: 45000,
    clicks: 1950,
    conversions: 180,
    ctr: 0.0433,
    cpa: 1050, // in 1000 - 7000 range
    cpm: 1020, // in 1000 - 7000 range
    spend: 3200, // in 1000 - 7000 range
    roas: 4.85,
    date_range: "Sep 01 - Sep 30, 2026",
    created_at: "2026-09-22T10:00:00+05:30",
    thumbnail_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=60",
    category: "Product Launch",
    target_audience: "Broad Audience",
    last_7_days_trend: [30, 25, 20, 15, 18, 14, 12],
  },
  {
    id: "camp_tiktok_warning",
    name: "Gen-Z Creator Campaign",
    platform: "tiktok",
    status: "WARNING",
    risk_score: 0.58,
    impressions: 82000,
    clicks: 2100,
    conversions: 95,
    ctr: 0.0256,
    cpa: 1380, // in 1000 - 7000 range
    cpm: 1150, // in 1000 - 7000 range
    spend: 4650, // in 1000 - 7000 range
    roas: 2.90,
    date_range: "Aug 10 - Sep 20, 2026",
    created_at: "2026-09-20T10:00:00+05:30",
    thumbnail_url: "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&auto=format&fit=crop&q=60",
    category: "Creator UGC",
    target_audience: "16-24 Short Video Viewers",
    last_7_days_trend: [45, 50, 62, 58, 70, 75, 85],
  },
];

export const HARDCODED_ALERTS = [
  {
    id: "alert-001",
    time: "2026-09-30T20:00:00+05:30",
    timestamp: "2026-09-30T20:00:00+05:30",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    alert: "Critical Fatigue Threshold Crossed (Audience Risk: 87%)",
    severity: "Critical",
    metric_impact: "Audience risk 0.87 • CTR -46% • CPA ₹1,450",
    metric_trend: [40, 52, 68, 76, 87],
    action_label: "Simulate Pause",
    action_type: "pause",
    status: "Open",
  },
  {
    id: "alert-002",
    time: "2026-09-30T18:00:00+05:30",
    timestamp: "2026-09-30T18:00:00+05:30",
    campaign_id: "camp_tiktok_warning",
    campaign_name: "Gen-Z Creator Campaign",
    platform: "tiktok",
    alert: "Warning Fatigue Alert: Audience Risk 58%",
    severity: "Warning",
    metric_impact: "Audience risk 0.58 • CTR -20% • CPA ₹1,380",
    metric_trend: [30, 38, 44, 52, 58],
    action_label: "Review Creative",
    action_type: "review",
    status: "Open",
  },
];

export const HARDCODED_RECOMMENDATIONS = [
  {
    id: "rec-001",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    action: "Pause Ad Creative Variant B",
    action_type: "pause",
    risk_level: "Critical (87%)",
    reason: "Fatigue mockery detected in 83% of comments with CTR collapse.",
    confidence: 0.96,
    impact: "Protects remaining ₹5,840 spend from negative brand perception.",
    can_execute: true,
  },
  {
    id: "rec-002",
    campaign_id: "camp_tiktok_warning",
    campaign_name: "Gen-Z Creator Campaign",
    action: "Rotate Audience & Refresh Hook",
    action_type: "rotate",
    risk_level: "Warning (58%)",
    reason: "Frequency rising past 3.2x with repeated exposure complaints.",
    confidence: 0.89,
    impact: "Stabilizes CPA around ₹1,380 before critical fatigue is reached.",
    can_execute: true,
  },
];

export const HARDCODED_RULES = [
  {
    id: "rule_critical_fatigue",
    name: "Critical Audience Fatigue Auto-Pause",
    condition: "Audience Risk >= 0.80 for 2 consecutive evaluations",
    action: "Simulated Pause + Alert Webhook",
    enabled: true,
    platform: "All Platforms",
    created_at: "2026-09-15T10:00:00+05:30",
  },
  {
    id: "rule_warning_alert",
    name: "Warning Slack Dispatch Guard",
    condition: "Audience Risk >= 0.60 or Negative Velocity >= 3.0x",
    action: "Notify #ad-ops on Slack",
    enabled: true,
    platform: "Meta & TikTok",
    created_at: "2026-09-18T10:00:00+05:30",
  },
];

export const HARDCODED_SETTINGS = {
  workspace_name: "AdFatigue Radar Workspace",
  currency: "INR",
  currency_symbol: "₹",
  timezone: "Asia/Kolkata",
  alert_threshold: 0.65,
  frequency_cap: 1.5,
  notification_in_app: true,
  notification_email: true,
  notification_slack: false,
  notification_webhooks: false,
};

export const HARDCODED_AUDIT_LOGS = [
  {
    audit_id: "AUDIT001",
    timestamp_simulated: "2026-09-30T10:00:00+05:30",
    actor_type: "SYSTEM",
    user_name: "System",
    event_type: "REPLAY_INITIALIZE",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    description: "Replay Session Initialized (72-hour window)",
    severity: "Info",
    action: "REPLAY_INITIALIZE",
    previous_state: "HEALTHY",
    new_state: "HEALTHY",
    reason_codes: ["SESSION_START"],
    risk: { fatigue_score: 18, audience_risk: 18 },
    readback_verified: true,
    config_version: "demo-v1",
  },
  {
    audit_id: "AUDIT002",
    timestamp_simulated: "2026-09-30T20:00:00+05:30",
    actor_type: "SYSTEM",
    user_name: "System",
    event_type: "RISK_THRESHOLD_CROSSED",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    description: "Risk Threshold Crossed: Critical (87%)",
    severity: "Critical",
    action: "RISK_THRESHOLD_CROSSED",
    previous_state: "WARNING",
    new_state: "CRITICAL",
    reason_codes: ["CTR_DECLINE", "NEGATIVE_SENTIMENT", "VELOCITY_SPIKE"],
    risk: { fatigue_score: 87, audience_risk: 87, cpa: 1450 },
    readback_verified: true,
    config_version: "demo-v1",
  },
  {
    audit_id: "AUDIT003",
    timestamp_simulated: "2026-09-30T20:05:00+05:30",
    actor_type: "SYSTEM",
    user_name: "System",
    event_type: "CREATE_ALERT",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    description: "Critical Alert Dispatched to Ad Ops",
    severity: "Warning",
    action: "CREATE_ALERT",
    previous_state: "CRITICAL",
    new_state: "CRITICAL",
    reason_codes: ["FATIGUE_SCORE_ABOVE_THRESHOLD"],
    risk: { fatigue_score: 87 },
    readback_verified: true,
    config_version: "demo-v1",
  },
  {
    audit_id: "AUDIT004",
    timestamp_simulated: "2026-09-30T20:10:00+05:30",
    actor_type: "AUTOMATION",
    user_name: "Automation Engine",
    event_type: "SIMULATED_PAUSE",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    description: "Simulated Campaign Pause Guardrail Activated",
    severity: "High",
    action: "SIMULATED_PAUSE",
    previous_state: "ACTIVE",
    new_state: "PAUSED",
    reason_codes: ["CRITICAL_FATIGUE", "GUARDRAIL_PASSED"],
    risk: { fatigue_score: 87, confidence: 0.96 },
    readback_verified: true,
    config_version: "demo-v1",
  },
  {
    audit_id: "AUDIT005",
    timestamp_simulated: "2026-09-30T20:11:00+05:30",
    actor_type: "SYSTEM",
    user_name: "System",
    event_type: "SLACK_NOTIFICATION",
    campaign_id: "camp_meta_fatigue",
    campaign_name: "Summer Creator Campaign",
    platform: "meta",
    description: "Slack Alert Dispatched to #ad-ops channel",
    severity: "Info",
    action: "SLACK_NOTIFICATION",
    previous_state: "PAUSED",
    new_state: "PAUSED",
    reason_codes: ["CRITICAL_ALERT"],
    risk: { notification: "sent" },
    readback_verified: true,
    config_version: "demo-v1",
  },
];

export const HARDCODED_ANALYTICS = {
  impressions: { value: 66600, change: -12.4, is_positive: false, sparkline: [5000, 5200, 5500, 5800, 6100] },
  clicks: { value: 1832, change: -70.8, is_positive: false, sparkline: [240, 215, 175, 125, 70] },
  conversions: { value: 143, change: -81.8, is_positive: false, sparkline: [22, 18, 14, 9, 4] },
  cpa: { value: 1450, change: 48.0, is_positive: false, sparkline: [1100, 1220, 1340, 1420, 1450] }, // in 1000-7000 range
  cpm: { value: 1120, change: 14.3, is_positive: false, sparkline: [1020, 1050, 1080, 1100, 1120] }, // in 1000-7000 range
  ctr: { value: 2.75, change: -76.0, is_positive: false, sparkline: [4.8, 4.1, 3.2, 2.2, 1.15] },
  performance_trend: [
    { date: "10:00", impressions: 5000, clicks: 240, conversions: 22, cpa: 1100, cpm: 1020, risk_score: 0.18 },
    { date: "11:00", impressions: 5100, clicks: 230, conversions: 20, cpa: 1140, cpm: 1030, risk_score: 0.24 },
    { date: "12:00", impressions: 5200, clicks: 215, conversions: 18, cpa: 1180, cpm: 1040, risk_score: 0.32 },
    { date: "13:00", impressions: 5300, clicks: 195, conversions: 16, cpa: 1220, cpm: 1050, risk_score: 0.40 },
    { date: "14:00", impressions: 5400, clicks: 175, conversions: 14, cpa: 1280, cpm: 1070, risk_score: 0.48 },
    { date: "15:00", impressions: 5500, clicks: 155, conversions: 12, cpa: 1350, cpm: 1090, risk_score: 0.58 },
    { date: "16:00", impressions: 5600, clicks: 140, conversions: 10, cpa: 1420, cpm: 1110, risk_score: 0.67 },
    { date: "17:00", impressions: 5700, clicks: 125, conversions: 9, cpa: 1490, cpm: 1130, risk_score: 0.72 },
    { date: "18:00", impressions: 5800, clicks: 110, conversions: 7, cpa: 1580, cpm: 1150, risk_score: 0.78 },
    { date: "19:00", impressions: 5900, clicks: 95, conversions: 6, cpa: 1690, cpm: 1180, risk_score: 0.82 },
    { date: "20:00", impressions: 6000, clicks: 82, conversions: 5, cpa: 1820, cpm: 1210, risk_score: 0.87 },
    { date: "21:00", impressions: 6100, clicks: 70, conversions: 4, cpa: 1950, cpm: 1250, risk_score: 0.91 },
  ],
  sentiment_overview: {
    total_comments: 12,
    positive_pct: 16.7,
    neutral_pct: 0.0,
    negative_pct: 83.3,
    spam_pct: 0.0,
    sentiment_decay: 0.88,
    fatigue_mockery: 0.94,
    comment_acceleration: 5.1,
  },
  risk_analysis: {
    audience_risk: 0.87,
    economic_risk: 0.82,
    state: "CRITICAL",
    description: "High negative sentiment velocity and severe CTR decline triggered automated guardrails.",
    thresholds: { watch: 0.40, warning: 0.60, soft: 0.70, critical: 0.80 },
  },
  platform_performance: [
    { platform: "meta", name: "Instagram / Meta", impressions: 111600, change_pct: -8.5, is_increase: false, color: "#0668E1" },
    { platform: "tiktok", name: "TikTok", impressions: 82000, change_pct: 14.2, is_increase: true, color: "#000000" },
  ],
  audience_insights: {
    age_groups: [
      { group: "18-24", percentage: 42 },
      { group: "25-34", percentage: 38 },
      { group: "35-44", percentage: 15 },
      { group: "45+", percentage: 5 },
    ],
    gender: { male: 44, female: 52, other: 4 },
  },
};

export const HARDCODED_COMPARISONS = {
  campaign_a: {
    id: "camp_meta_fatigue",
    name: "Summer Creator Campaign",
    platform: "meta",
    category: "Summer Apparel",
    thumbnail: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
    impressions: 66600,
    clicks: 1832,
    conversions: 143,
    cpa: 1450, // in 1000 - 7000 range
    cpm: 1120, // in 1000 - 7000 range
    ctr: 2.75,
    sentiment_decay: 0.88,
    negative_ratio: 83.3,
    comment_acceleration: 5.1,
    ctr_frequency: 0.42,
    critical_complaints: 1,
    sentiment: { positive: 16.7, neutral: 0.0, negative: 83.3 },
  },
  campaign_b: {
    id: "camp_meta_healthy",
    name: "Product Launch Campaign",
    platform: "meta",
    category: "Product Launch",
    thumbnail: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=60",
    impressions: 45000,
    clicks: 1950,
    conversions: 180,
    cpa: 1050, // in 1000 - 7000 range
    cpm: 1020, // in 1000 - 7000 range
    ctr: 4.33,
    sentiment_decay: 0.05,
    negative_ratio: 5.0,
    comment_acceleration: 0.2,
    ctr_frequency: 0.08,
    critical_complaints: 0,
    sentiment: { positive: 85.0, neutral: 10.0, negative: 5.0 },
  },
  risk_timeline: [
    { date: "10:00", risk_a: 0.18, risk_b: 0.10 },
    { date: "12:00", risk_a: 0.32, risk_b: 0.11 },
    { date: "14:00", risk_a: 0.48, risk_b: 0.12 },
    { date: "16:00", risk_a: 0.67, risk_b: 0.12 },
    { date: "18:00", risk_a: 0.78, risk_b: 0.13 },
    { date: "20:00", risk_a: 0.87, risk_b: 0.12 },
    { date: "21:00", risk_a: 0.91, risk_b: 0.12 },
  ],
  platform_breakdown: [],
  top_comment_categories: [
    { category: "AD_FATIGUE", pct_a: 83.3, pct_b: 0.0 },
    { category: "GENERAL_POSITIVE", pct_a: 16.7, pct_b: 85.0 },
    { category: "PRICE_COMPLAINT", pct_a: 8.3, pct_b: 5.0 },
  ],
  insights: [
    "Summer Creator Campaign displays severe ad fatigue: CTR dropped 76% while CPA inflated to ₹1,450.",
    "Product Launch Campaign remains healthy with 85% positive reactions and stable ₹1,050 CPA.",
  ],
};

export const HARDCODED_REPLAY_SNAPSHOT = {
  campaign_id: "camp_meta_fatigue",
  scenario_name: "Summer Creator Fatigue Replay",
  seed: 42,
  current_hour: 11,
  simulated_timestamp: "2026-09-30T21:00:00+05:30",
  is_running: false,
  speed: 1.0,
  current_state: "CRITICAL",
  previous_state: "WARNING",
  state_reason: "CRITICAL_FATIGUE,GUARDRAIL_PASSED",
  points: [
    { hour: 0, timestamp_simulated: "2026-09-30T10:00:00+05:30", potential_impressions: 5000, observed_impressions: 5000, potential_spend: 2400, observed_spend: 2400, audience_risk: 0.18, economic_risk: 0.15, cpa: 1100, cpm: 1020, state: "HEALTHY" },
    { hour: 2, timestamp_simulated: "2026-09-30T12:00:00+05:30", potential_impressions: 10300, observed_impressions: 10300, potential_spend: 3200, observed_spend: 3200, audience_risk: 0.32, economic_risk: 0.28, cpa: 1180, cpm: 1040, state: "WATCH" },
    { hour: 4, timestamp_simulated: "2026-09-30T14:00:00+05:30", potential_impressions: 21000, observed_impressions: 21000, potential_spend: 4100, observed_spend: 4100, audience_risk: 0.48, economic_risk: 0.43, cpa: 1280, cpm: 1070, state: "WATCH" },
    { hour: 6, timestamp_simulated: "2026-09-30T16:00:00+05:30", potential_impressions: 32100, observed_impressions: 32100, potential_spend: 5200, observed_spend: 5200, audience_risk: 0.67, economic_risk: 0.61, cpa: 1420, cpm: 1110, state: "WARNING" },
    { hour: 8, timestamp_simulated: "2026-09-30T18:00:00+05:30", potential_impressions: 43600, observed_impressions: 43600, potential_spend: 5840, observed_spend: 5840, audience_risk: 0.78, economic_risk: 0.73, cpa: 1580, cpm: 1150, state: "WARNING" },
    { hour: 10, timestamp_simulated: "2026-09-30T20:00:00+05:30", potential_impressions: 55500, observed_impressions: 55500, potential_spend: 6400, observed_spend: 5840, audience_risk: 0.87, economic_risk: 0.82, cpa: 1820, cpm: 1210, state: "CRITICAL" },
    { hour: 11, timestamp_simulated: "2026-09-30T21:00:00+05:30", potential_impressions: 61600, observed_impressions: 61600, potential_spend: 6900, observed_spend: 5840, audience_risk: 0.91, economic_risk: 0.88, cpa: 1950, cpm: 1250, state: "CRITICAL" },
  ],
  live_comments: [
    { id: "c-1", author: "User @fashion_fan", text: "Stop showing me this ad again 🙄", sentiment: "NEGATIVE", category: "fatigue" },
    { id: "c-2", author: "User @insta_shopper", text: "I have seen this like ten times already", sentiment: "NEGATIVE", category: "fatigue" },
    { id: "c-3", author: "User @apparel_guy", text: "Quality looks nice though", sentiment: "POSITIVE", category: "positive" },
  ],
  actions_history: [
    { action: "SIMULATED_PAUSE", time: "20:10", state: "PAUSED", reason: "Fatigue score 87 above critical threshold" }
  ],
  audit_trail: HARDCODED_AUDIT_LOGS,
};
