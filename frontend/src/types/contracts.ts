export type CampaignState = 
  | "ACTIVE" 
  | "WATCH" 
  | "WARNING" 
  | "SOFT_REDUCED" 
  | "PAUSED" 
  | "BLOCKED" 
  | "COMPLETED";

export type Platform = "meta" | "google" | "tiktok" | "youtube" | "x";

export type CommentCategory = 
  | "product_complaint" 
  | "service_complaint" 
  | "fatigue" 
  | "mockery" 
  | "spam" 
  | "banter_meme" 
  | "neutral" 
  | "positive";

export type Severity = "critical" | "warning" | "info" | "high" | "medium" | "low" | "resolved";

export interface CommentEvent {
  event_id: string;
  timestamp: string;
  campaign_id: string;
  ad_id: string;
  author_id: string;
  author_name?: string;
  avatar_seed?: string;
  text: string;
  reactions: number;
  replies: number;
  sentiment: "positive" | "neutral" | "negative";
  sentiment_score: number;
  category: CommentCategory;
  confidence: number;
  critical_complaint: boolean;
}

export interface TelemetryEvent {
  event_id: string;
  timestamp: string;
  campaign_id: string;
  ad_id: string;
  spend: number;
  impressions: number;
  reach: number;
  clicks: number;
  conversions: number;
  cpm: number;
  cpc: number;
  cpa: number | null; // CPA null when conversions = 0
  roas: number;
}

export interface RiskSnapshot {
  audience_risk: number;
  economic_risk: number | null; // N/A if < 20 conversions in window
  harmful_ratio: number;
  wilson_lower_bound: number;
  sentiment_decay: number;
  fatigue_mockery: number;
  comment_acceleration: number;
  ctr_frequency: number;
  critical_complaint_rate: number;
  timestamp: string;
}

export interface Campaign {
  id: string;
  name: string;
  platform: Platform;
  status: CampaignState;
  risk_score: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cpa: number | null;
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

export interface ReplayTimelinePoint {
  hour: number;
  timestamp_simulated: string;
  potential_impressions: number;
  observed_impressions: number;
  potential_spend: number;
  observed_spend: number;
  audience_risk: number;
  economic_risk: number | null;
  cpa: number | null;
  cpm: number;
  state: CampaignState;
  events?: string[];
  action_applied?: string;
}

export interface ReplayState {
  campaign_id: string;
  scenario_name: string;
  seed: number;
  current_hour: number;
  simulated_timestamp: string;
  is_running: boolean;
  speed: number;
  current_state: CampaignState;
  previous_state?: CampaignState;
  state_reason?: string;
  points: ReplayTimelinePoint[];
  live_comments: CommentEvent[];
  actions_history: ActionHistoryItem[];
  audit_trail: AuditEvent[];
}

export interface ActionHistoryItem {
  id: string;
  action: "WARNING" | "SOFT_REDUCED" | "PAUSE" | "READBACK_VERIFIED" | "RESUME" | "AUDIT_LOGGED";
  mode: "SANDBOX" | "LIVE";
  executed: boolean;
  confidence: number;
  reason: string;
  previous_state: CampaignState;
  new_state: CampaignState;
  readback_verified: boolean;
  audit_event_id: string;
  timestamp: string;
}

export interface AuditEvent {
  audit_id: string;
  timestamp_simulated: string;
  actor_type: "USER" | "SYSTEM" | "AI_BOT";
  user_name: string;
  user_avatar?: string;
  event_type: string;
  campaign_id: string;
  campaign_name: string;
  platform: Platform;
  description: string;
  severity: "Critical" | "High" | "Medium" | "Low" | "Info";
  action?: string;
  previous_state?: CampaignState;
  new_state?: CampaignState;
  reason_codes?: string[];
  risk?: {
    audience_risk: number;
    economic_risk: number | null;
  };
  readback_verified?: boolean;
  config_version?: string;
  details?: Record<string, unknown>;
}

export interface AlertItem {
  id: string;
  time: string;
  timestamp: string;
  campaign_id: string;
  campaign_name: string;
  platform: Platform;
  alert: string;
  severity: "Critical" | "Warning" | "Info";
  metric_impact: string;
  metric_trend: number[];
  action_label: "View" | "Take Action";
  action_type: "pause" | "reduce_frequency" | "switch_creative" | "filter_comments" | "inspect";
  status: "Open" | "Investigating" | "Resolved";
}

export interface RecommendedAction {
  id: string;
  title: string;
  description: string;
  button_label: string;
  button_variant: "red" | "orange" | "blue" | "green" | "purple";
  icon_name: string;
  campaign_id?: string;
  action_type: string;
}

export interface AutomationRule {
  id: string;
  title: string;
  description: string;
  enabled: boolean;
  icon_name: string;
}

export interface SettingsData {
  workspace: {
    name: string;
    account_tier: string;
    active_members: number;
    alert_channels: number;
    connected_integrations: number;
    data_retention_months: number;
    plan: string;
  };
  profile: {
    account_name: string;
    email: string;
    organization: string;
    time_zone: string;
    language: string;
  };
  notification_preferences: {
    in_app: { enabled: boolean; critical: boolean; warning: boolean; info: boolean };
    email: { enabled: boolean; critical: boolean; warning: boolean; info: boolean };
    slack: { enabled: boolean; critical: boolean; warning: boolean; info: boolean };
    webhooks: { enabled: boolean; critical: boolean; warning: boolean; info: boolean };
  };
  default_campaign_settings: {
    default_platform: Platform;
    default_audience_type: string;
    default_monitoring_duration_days: number;
    default_alert_threshold: number;
    currency: string;
    frequency_cap: number;
  };
  monitoring_rules: {
    audience_fatigue_risk: { warn_at: number; critical_at: number; current_value: number; trend: number[] };
    sentiment_decay: { warn_at: number; critical_at: number; current_value: number; trend: number[] };
    negative_comment_ratio: { warn_at: number; critical_at: number; current_value: number; trend: number[] };
    cpa_increase: { warn_at: number; critical_at: number; current_value: number; trend: number[] };
  };
  integrations: Array<{
    id: string;
    name: string;
    platform: Platform | "slack" | "webhook";
    connected: boolean;
    account_handle?: string;
  }>;
  team_members: Array<{
    id: string;
    name: string;
    email: string;
    role: "Owner" | "Admin" | "Analyst" | "Viewer";
    avatar_initials: string;
    access_level: "Full Access" | "Analytics Only" | "Read Only";
  }>;
  data_privacy: {
    event_log_retention_months: number;
    comment_data_retention_months: number;
    anonymize_user_data: boolean;
    gdpr_compliance: boolean;
  };
}
