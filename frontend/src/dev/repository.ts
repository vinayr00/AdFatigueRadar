import {
  Campaign,
  CampaignState,
  CommentEvent,
  ReplayTimelinePoint,
  ReplayState,
  ActionHistoryItem,
  AuditEvent,
  AlertItem,
  RecommendedAction,
  AutomationRule,
  SettingsData,
} from "../types/contracts";

export class DevRepository {
  private campaigns: Campaign[] = [
    {
      id: "cmp_summer_2024",
      name: "Summer Collection 2024",
      platform: "meta",
      status: "WARNING",
      risk_score: 0.72,
      impressions: 1200000,
      clicks: 16800,
      conversions: 312,
      ctr: 1.4,
      cpa: 18.40,
      cpm: 9.10,
      spend: 5740.80,
      roas: 3.4,
      date_range: "Jun 12, 2024 – Jul 12, 2024",
      created_at: "2024-06-12T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=120&q=80",
      category: "Fashion & Apparel",
      target_audience: "Broad 18-45",
      last_7_days_trend: [0.35, 0.42, 0.51, 0.58, 0.64, 0.69, 0.72],
    },
    {
      id: "cmp_monsoon_sale",
      name: "Monsoon Sale",
      platform: "google",
      status: "ACTIVE",
      risk_score: 0.28,
      impressions: 850000,
      clicks: 12100,
      conversions: 210,
      ctr: 2.1,
      cpa: 12.30,
      cpm: 7.20,
      spend: 2583.00,
      roas: 4.6,
      date_range: "May 10, 2024 – Jun 10, 2024",
      created_at: "2024-05-10T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=120&q=80",
      category: "Seasonal Campaign",
      target_audience: "In-Market Shoppers",
      last_7_days_trend: [0.22, 0.24, 0.25, 0.26, 0.27, 0.27, 0.28],
    },
    {
      id: "cmp_new_product",
      name: "New Product Launch",
      platform: "meta",
      status: "ACTIVE",
      risk_score: 0.41,
      impressions: 620000,
      clicks: 11160,
      conversions: 184,
      ctr: 1.8,
      cpa: 15.20,
      cpm: 8.50,
      spend: 2796.80,
      roas: 3.8,
      date_range: "Apr 01, 2024 – May 01, 2024",
      created_at: "2024-04-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80",
      category: "Product Launch",
      target_audience: "Tech Enthusiasts",
      last_7_days_trend: [0.28, 0.31, 0.35, 0.38, 0.39, 0.40, 0.41],
    },
    {
      id: "cmp_retargeting_web",
      name: "Retargeting – Website",
      platform: "google",
      status: "PAUSED",
      risk_score: 0.18,
      impressions: 420000,
      clicks: 7980,
      conversions: 160,
      ctr: 1.9,
      cpa: 10.50,
      cpm: 6.80,
      spend: 1680.00,
      roas: 5.2,
      date_range: "Mar 15, 2024 – Apr 15, 2024",
      created_at: "2024-03-15T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&q=80",
      category: "Retargeting",
      target_audience: "Website Visitors (30d)",
      last_7_days_trend: [0.18, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18],
    },
    {
      id: "cmp_festive_offers",
      name: "Festive Offers",
      platform: "meta",
      status: "COMPLETED",
      risk_score: 0.35,
      impressions: 950000,
      clicks: 21850,
      conversions: 380,
      ctr: 2.3,
      cpa: 11.80,
      cpm: 7.90,
      spend: 4484.00,
      roas: 4.9,
      date_range: "Nov 01, 2023 – Dec 15, 2023",
      created_at: "2023-11-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=120&q=80",
      category: "Holiday Promo",
      target_audience: "Festive Buyers",
      last_7_days_trend: [0.32, 0.33, 0.34, 0.35, 0.35, 0.35, 0.35],
    },
    {
      id: "cmp_retargeting_q2",
      name: "Retargeting – Q2",
      platform: "youtube",
      status: "WARNING",
      risk_score: 0.65,
      impressions: 420000,
      clicks: 5040,
      conversions: 98,
      ctr: 1.2,
      cpa: 20.50,
      cpm: 12.10,
      spend: 2009.00,
      roas: 2.7,
      date_range: "Apr 15, 2024 – Jun 15, 2024",
      created_at: "2024-04-15T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&q=80",
      category: "Video Retargeting",
      target_audience: "Video Viewers 50%+",
      last_7_days_trend: [0.45, 0.50, 0.54, 0.58, 0.61, 0.63, 0.65],
    },
    {
      id: "cmp_flash_deal",
      name: "Flash Weekend Deal",
      platform: "tiktok",
      status: "WARNING",
      risk_score: 0.71,
      impressions: 620000,
      clicks: 9300,
      conversions: 142,
      ctr: 1.5,
      cpa: 18.10,
      cpm: 8.90,
      spend: 2570.20,
      roas: 3.1,
      date_range: "May 20, 2024 – Jun 02, 2024",
      created_at: "2024-05-20T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&q=80",
      category: "Flash Sale",
      target_audience: "Gen-Z Shoppers",
      last_7_days_trend: [0.40, 0.48, 0.55, 0.62, 0.67, 0.70, 0.71],
    },
    {
      id: "cmp_holiday_early_bird",
      name: "Holiday Early Bird",
      platform: "meta",
      status: "ACTIVE",
      risk_score: 0.22,
      impressions: 1100000,
      clicks: 26400,
      conversions: 420,
      ctr: 2.4,
      cpa: 11.20,
      cpm: 7.10,
      spend: 4704.00,
      roas: 5.1,
      date_range: "May 01, 2024 – Jun 30, 2024",
      created_at: "2024-05-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=120&q=80",
      category: "Early Access",
      target_audience: "Past Purchasers",
      last_7_days_trend: [0.20, 0.21, 0.21, 0.22, 0.22, 0.22, 0.22],
    },
    {
      id: "cmp_brand_refresh",
      name: "Spring Brand Refresh",
      platform: "google",
      status: "ACTIVE",
      risk_score: 0.19,
      impressions: 780000,
      clicks: 15600,
      conversions: 290,
      ctr: 2.0,
      cpa: 13.40,
      cpm: 8.20,
      spend: 3886.00,
      roas: 4.3,
      date_range: "Mar 01, 2024 – May 30, 2024",
      created_at: "2024-03-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=120&q=80",
      category: "Brand Awareness",
      target_audience: "Urban Professionals",
      last_7_days_trend: [0.18, 0.18, 0.19, 0.19, 0.19, 0.19, 0.19],
    },
    {
      id: "cmp_loyalty_drop",
      name: "VIP Loyalty Drop",
      platform: "tiktok",
      status: "ACTIVE",
      risk_score: 0.32,
      impressions: 540000,
      clicks: 14580,
      conversions: 260,
      ctr: 2.7,
      cpa: 14.10,
      cpm: 9.20,
      spend: 3666.00,
      roas: 4.7,
      date_range: "May 15, 2024 – Jun 15, 2024",
      created_at: "2024-05-15T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=120&q=80",
      category: "Loyalty Promo",
      target_audience: "VIP Tier Members",
      last_7_days_trend: [0.28, 0.29, 0.30, 0.31, 0.31, 0.32, 0.32],
    },
    {
      id: "cmp_app_install",
      name: "App Install Push",
      platform: "youtube",
      status: "ACTIVE",
      risk_score: 0.29,
      impressions: 890000,
      clicks: 14240,
      conversions: 410,
      ctr: 1.6,
      cpa: 9.80,
      cpm: 6.40,
      spend: 4018.00,
      roas: 4.8,
      date_range: "Apr 01, 2024 – Jun 30, 2024",
      created_at: "2024-04-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=120&q=80",
      category: "App Growth",
      target_audience: "Mobile Gamers",
      last_7_days_trend: [0.25, 0.26, 0.27, 0.28, 0.28, 0.29, 0.29],
    },
    {
      id: "cmp_cart_recovery",
      name: "Cart Recovery Blitz",
      platform: "meta",
      status: "ACTIVE",
      risk_score: 0.26,
      impressions: 450000,
      clicks: 13950,
      conversions: 320,
      ctr: 3.1,
      cpa: 8.90,
      cpm: 7.40,
      spend: 2848.00,
      roas: 5.6,
      date_range: "May 01, 2024 – Jun 15, 2024",
      created_at: "2024-05-01T00:00:00Z",
      thumbnail_url: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=120&q=80",
      category: "Dynamic Retargeting",
      target_audience: "Abandon Cart 7d",
      last_7_days_trend: [0.22, 0.23, 0.24, 0.25, 0.25, 0.26, 0.26],
    },
  ];

  public getCampaigns(filters?: { status?: string; platform?: string; search?: string }): Campaign[] {
    let list = [...this.campaigns];
    if (filters?.status && filters.status !== "all" && filters.status !== "All Campaigns") {
      list = list.filter((c) => c.status.toLowerCase() === filters.status?.toLowerCase());
    }
    if (filters?.platform && filters.platform !== "all" && filters.platform !== "All Platforms") {
      list = list.filter((c) => c.platform.toLowerCase() === filters.platform?.toLowerCase());
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      list = list.filter((c) => c.name.toLowerCase().includes(q) || c.category.toLowerCase().includes(q));
    }
    return list;
  }

  public getCampaignById(id: string): Campaign | null {
    return this.campaigns.find((c) => c.id === id) || this.campaigns[0] || null;
  }

  public createCampaign(data: Partial<Campaign>): Campaign {
    const newCamp: Campaign = {
      id: `cmp_${Date.now()}`,
      name: data.name || "Untitled Campaign",
      platform: data.platform || "meta",
      status: "ACTIVE",
      risk_score: 0.15,
      impressions: 0,
      clicks: 0,
      conversions: 0,
      ctr: 0.0,
      cpa: null,
      cpm: 8.0,
      spend: 0,
      roas: 0,
      date_range: data.date_range || "Today – Next 30 Days",
      created_at: new Date().toISOString(),
      thumbnail_url: data.thumbnail_url || "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=120&q=80",
      category: data.category || "General Campaign",
      target_audience: data.target_audience || "Broad Audience",
      last_7_days_trend: [0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
    };
    this.campaigns.unshift(newCamp);
    return newCamp;
  }

  public pauseCampaign(campaignId: string): { success: boolean; new_state: CampaignState; readback_verified: boolean } {
    const camp = this.campaigns.find((c) => c.id === campaignId);
    if (camp) {
      camp.status = "PAUSED";
    }
    return {
      success: true,
      new_state: "PAUSED",
      readback_verified: true,
    };
  }

  public unpauseCampaign(campaignId: string): { success: boolean; new_state: CampaignState; readback_verified: boolean } {
    const camp = this.campaigns.find((c) => c.id === campaignId);
    if (camp) {
      camp.status = "ACTIVE";
    }
    return {
      success: true,
      new_state: "ACTIVE",
      readback_verified: true,
    };
  }

  public getReplayData(campaignId: string = "cmp_summer_2024", speed: number = 1): ReplayState {
    const points: ReplayTimelinePoint[] = [];
    const baseDate = new Date("2024-06-12T00:00:00Z");

    for (let h = 0; h <= 72; h += 2) {
      const simulatedTime = new Date(baseDate.getTime() + h * 3600 * 1000).toISOString();
      let state: CampaignState = "ACTIVE";
      let action: string | undefined = undefined;
      let audRisk = 0.15;
      let econRisk: number | null = null;
      let cpa: number | null = null;
      let potImp = 16000 + Math.sin(h / 6) * 4000;
      let obsImp = potImp;
      let potSpend = 80 + (h * 1.5);
      let obsSpend = potSpend;

      if (h < 18) {
        // Healthy Phase
        audRisk = 0.15 + (h / 18) * 0.12;
        econRisk = 0.12;
        cpa = 14.20 + Math.sin(h) * 1.2;
        state = "ACTIVE";
      } else if (h < 36) {
        // Fatigue Onset
        audRisk = 0.27 + ((h - 18) / 18) * 0.38; // crosses 0.65 around h=28
        econRisk = 0.25 + ((h - 18) / 18) * 0.18;
        cpa = 16.50 + ((h - 18) / 18) * 4.0;
        state = audRisk >= 0.65 ? "WARNING" : "WATCH";
        if (h === 28) action = "WARNING_TRIGGERED";
      } else if (h < 52) {
        // Acceleration -> SOFT_REDUCED
        audRisk = 0.65 + ((h - 36) / 16) * 0.16;
        econRisk = 0.43 + ((h - 36) / 16) * 0.25;
        state = "SOFT_REDUCED";
        obsImp = potImp * 0.80; // 0.80x multiplier per spec
        obsSpend = potSpend * 0.80;
        cpa = 21.0 + ((h - 36) / 16) * 6.5;
        if (h === 42) action = "SOFT_BUDGET_APPLIED";
      } else {
        // Economic Degradation -> PAUSED
        audRisk = 0.81 + ((h - 52) / 20) * 0.14;
        econRisk = 0.68 + ((h - 52) / 20) * 0.22;
        cpa = 28.0 + ((h - 52) / 20) * 12.0;
        if (h >= 58) {
          state = "PAUSED";
          obsImp = 0; // zero-volume heartbeat
          obsSpend = 0;
          if (h === 58) action = "CAMPAIGN_PAUSED";
          if (h === 60) action = "READBACK_VERIFIED";
        } else {
          state = "SOFT_REDUCED";
          obsImp = potImp * 0.80;
          obsSpend = potSpend * 0.80;
        }
      }

      points.push({
        hour: h,
        timestamp_simulated: simulatedTime,
        potential_impressions: Math.round(potImp),
        observed_impressions: Math.round(obsImp),
        potential_spend: Number(potSpend.toFixed(2)),
        observed_spend: Number(obsSpend.toFixed(2)),
        audience_risk: Number(audRisk.toFixed(2)),
        economic_risk: econRisk !== null ? Number(econRisk.toFixed(2)) : null,
        cpa: obsImp > 0 ? Number(cpa?.toFixed(2) ?? null) : null,
        cpm: 9.10,
        state,
        events: action ? [action] : undefined,
        action_applied: action,
      });
    }

    const liveComments: CommentEvent[] = [
      {
        event_id: "cmt_101",
        timestamp: "2024-06-13T14:31:00Z",
        campaign_id: campaignId,
        ad_id: "ad_summer_01",
        author_id: "usr_hmac_83a1",
        author_name: "Sarah M.",
        avatar_seed: "sarah",
        text: "I have seen this same exact dress ad 10 times today already... please make it stop 🙄",
        reactions: 42,
        replies: 11,
        sentiment: "negative",
        sentiment_score: 0.94,
        category: "fatigue",
        confidence: 0.96,
        critical_complaint: false,
      },
      {
        event_id: "cmt_102",
        timestamp: "2024-06-13T14:28:10Z",
        campaign_id: campaignId,
        ad_id: "ad_summer_02",
        author_id: "usr_hmac_491b",
        author_name: "Jason K.",
        avatar_seed: "jason",
        text: "The shipping took 4 weeks and customer service ignored all my emails.",
        reactions: 19,
        replies: 5,
        sentiment: "negative",
        sentiment_score: 0.91,
        category: "service_complaint",
        confidence: 0.93,
        critical_complaint: true,
      },
      {
        event_id: "cmt_103",
        timestamp: "2024-06-13T14:24:45Z",
        campaign_id: campaignId,
        ad_id: "ad_summer_01",
        author_id: "usr_hmac_92d7",
        author_name: "MemeLord99",
        avatar_seed: "meme",
        text: "Bro is haunting my feed in my dreams too at this point 😂💀",
        reactions: 88,
        replies: 23,
        sentiment: "negative",
        sentiment_score: 0.85,
        category: "mockery",
        confidence: 0.91,
        critical_complaint: false,
      },
      {
        event_id: "cmt_104",
        timestamp: "2024-06-13T14:18:20Z",
        campaign_id: campaignId,
        ad_id: "ad_summer_03",
        author_id: "usr_hmac_12a8",
        author_name: "Elena R.",
        avatar_seed: "elena",
        text: "The fabric quality on the linen shirt is actually pretty great, arrived in 2 days.",
        reactions: 14,
        replies: 2,
        sentiment: "positive",
        sentiment_score: 0.89,
        category: "positive",
        confidence: 0.95,
        critical_complaint: false,
      },
      {
        event_id: "cmt_105",
        timestamp: "2024-06-13T14:12:00Z",
        campaign_id: campaignId,
        ad_id: "ad_summer_01",
        author_id: "usr_hmac_77e3",
        author_name: "CryptoBot_99",
        avatar_seed: "bot",
        text: "Check my bio for instant $500 crypto giveaway fast click here!",
        reactions: 1,
        replies: 0,
        sentiment: "negative",
        sentiment_score: 0.70,
        category: "spam",
        confidence: 0.98,
        critical_complaint: false,
      },
    ];

    const actionsHistory: ActionHistoryItem[] = [
      {
        id: "act_001",
        action: "WARNING",
        mode: "SANDBOX",
        executed: true,
        confidence: 0.94,
        reason: "Audience fatigue crossed warning threshold (0.65) with Wilson lower bound 0.58",
        previous_state: "WATCH",
        new_state: "WARNING",
        readback_verified: true,
        audit_event_id: "audit_0018",
        timestamp: "2024-06-13T14:28:04Z",
      },
      {
        id: "act_002",
        action: "SOFT_REDUCED",
        mode: "SANDBOX",
        executed: true,
        confidence: 0.91,
        reason: "Sustained harmful fatigue acceleration; frequency multiplier scaled to 0.80x",
        previous_state: "WARNING",
        new_state: "SOFT_REDUCED",
        readback_verified: true,
        audit_event_id: "audit_0024",
        timestamp: "2024-06-13T14:15:31Z",
      },
      {
        id: "act_003",
        action: "PAUSE",
        mode: "SANDBOX",
        executed: true,
        confidence: 0.96,
        reason: "Economic confirmation gate satisfied: CPA spike +40% with fatigue score 0.72",
        previous_state: "SOFT_REDUCED",
        new_state: "PAUSED",
        readback_verified: true,
        audit_event_id: "audit_0041",
        timestamp: "2024-06-13T14:32:18Z",
      },
    ];

    return {
      campaign_id: campaignId,
      scenario_name: "Standard Fatigue Run (Seed #42)",
      seed: 42,
      current_hour: 38.5,
      simulated_timestamp: "2024-06-13T14:30:00Z",
      is_running: false,
      speed,
      current_state: "WARNING",
      previous_state: "WATCH",
      state_reason: "Audience fatigue risk is elevated. Negative sentiment and comment volume are increasing.",
      points,
      live_comments: liveComments,
      actions_history: actionsHistory,
      audit_trail: this.getAuditEvents(),
    };
  }

  public getAuditEvents(): AuditEvent[] {
    return [
      {
        audit_id: "audit_001",
        timestamp_simulated: "2024-06-30T14:32:18Z",
        actor_type: "USER",
        user_name: "Aditya Sharma",
        user_avatar: "AD",
        event_type: "Campaign Action",
        campaign_id: "cmp_summer_2024",
        campaign_name: "Summer Collection 2024",
        platform: "meta",
        description: "Paused campaign due to high fatigue risk (0.72).",
        severity: "High",
        action: "PAUSE",
        previous_state: "WARNING",
        new_state: "PAUSED",
        reason_codes: ["AUDIENCE_RISK_HIGH", "USER_OVERRIDE"],
        readback_verified: true,
        config_version: "thresholds_v4",
      },
      {
        audit_id: "audit_002",
        timestamp_simulated: "2024-06-30T14:28:04Z",
        actor_type: "SYSTEM",
        user_name: "System",
        event_type: "Alert Triggered",
        campaign_id: "cmp_summer_2024",
        campaign_name: "Summer Collection 2024",
        platform: "meta",
        description: "Audience fatigue crossed warning threshold (0.65).",
        severity: "High",
        reason_codes: ["THRESHOLD_BREACH_WARNING"],
        readback_verified: true,
        config_version: "thresholds_v4",
      },
      {
        audit_id: "audit_003",
        timestamp_simulated: "2024-06-30T14:15:31Z",
        actor_type: "AI_BOT",
        user_name: "AI Bot",
        event_type: "Auto Action",
        campaign_id: "cmp_monsoon_sale",
        campaign_name: "Monsoon Sale",
        platform: "google",
        description: "Reduced ad frequency (1.5 → 1.0).",
        severity: "Medium",
        action: "SOFT_REDUCED",
        readback_verified: true,
        config_version: "thresholds_v4",
      },
      {
        audit_id: "audit_004",
        timestamp_simulated: "2024-06-30T13:52:10Z",
        actor_type: "USER",
        user_name: "Priya Reddy",
        user_avatar: "PR",
        event_type: "Settings Change",
        campaign_id: "cmp_festive_offers",
        campaign_name: "Festive Offers",
        platform: "tiktok",
        description: "Updated comment filter (added 3 new keywords).",
        severity: "Low",
        reason_codes: ["KEYWORD_FILTER_UPDATE"],
      },
      {
        audit_id: "audit_005",
        timestamp_simulated: "2024-06-30T12:41:05Z",
        actor_type: "SYSTEM",
        user_name: "System",
        event_type: "Data Ingestion",
        campaign_id: "all",
        campaign_name: "All Campaigns",
        platform: "meta",
        description: "Processed 12.4K new comments from Meta Ads API.",
        severity: "Info",
        reason_codes: ["INGESTION_BATCH_SUCCESS"],
      },
      {
        audit_id: "audit_006",
        timestamp_simulated: "2024-06-30T11:20:33Z",
        actor_type: "USER",
        user_name: "Rohit Verma",
        user_avatar: "RV",
        event_type: "Rule Updated",
        campaign_id: "cmp_monsoon_sale",
        campaign_name: "Monsoon Sale",
        platform: "google",
        description: "Enabled auto-pause rule (risk > 0.85).",
        severity: "Medium",
      },
      {
        audit_id: "audit_007",
        timestamp_simulated: "2024-06-30T10:15:21Z",
        actor_type: "AI_BOT",
        user_name: "AI Bot",
        event_type: "Insight Generated",
        campaign_id: "cmp_summer_2024",
        campaign_name: "Summer Collection 2024",
        platform: "meta",
        description: "Detected 42% increase in negative sentiment.",
        severity: "Info",
      },
      {
        audit_id: "audit_008",
        timestamp_simulated: "2024-06-30T09:48:12Z",
        actor_type: "USER",
        user_name: "Neha Kapoor",
        user_avatar: "NK",
        event_type: "Campaign Edit",
        campaign_id: "cmp_retargeting_q2",
        campaign_name: "Retargeting – Q2",
        platform: "youtube",
        description: "Updated budget $20 → $35 per day.",
        severity: "Low",
      },
      {
        audit_id: "audit_009",
        timestamp_simulated: "2024-06-30T08:22:45Z",
        actor_type: "SYSTEM",
        user_name: "System",
        event_type: "Retrain Model",
        campaign_id: "all",
        campaign_name: "All Campaigns",
        platform: "meta",
        description: "Sentiment model retrained with 25K new samples.",
        severity: "Info",
      },
      {
        audit_id: "audit_010",
        timestamp_simulated: "2024-06-30T07:10:18Z",
        actor_type: "AI_BOT",
        user_name: "AI Bot",
        event_type: "Auto Action",
        campaign_id: "cmp_new_product",
        campaign_name: "New Product Launch",
        platform: "meta",
        description: "Sent Slack alert to team (critical comments spike).",
        severity: "High",
      },
    ];
  }

  public getAlerts(): AlertItem[] {
    return [
      {
        id: "alt_001",
        time: "2 min ago",
        timestamp: "2024-06-30T14:32:00Z",
        campaign_id: "cmp_summer_2024",
        campaign_name: "Summer Collection 2024",
        platform: "meta",
        alert: "Audience fatigue crossed warning threshold (0.65)",
        severity: "Critical",
        metric_impact: "Risk: 0.72 (+28%)",
        metric_trend: [0.55, 0.58, 0.62, 0.65, 0.68, 0.70, 0.72],
        action_label: "View",
        action_type: "inspect",
        status: "Open",
      },
      {
        id: "alt_002",
        time: "12 min ago",
        timestamp: "2024-06-30T14:22:00Z",
        campaign_id: "cmp_monsoon_sale",
        campaign_name: "Monsoon Sale",
        platform: "google",
        alert: "Negative sentiment spike detected",
        severity: "Warning",
        metric_impact: "Neg. Ratio: 24% (+52%)",
        metric_trend: [0.15, 0.16, 0.18, 0.20, 0.22, 0.23, 0.24],
        action_label: "Take Action",
        action_type: "reduce_frequency",
        status: "Open",
      },
      {
        id: "alt_003",
        time: "28 min ago",
        timestamp: "2024-06-30T14:06:00Z",
        campaign_id: "cmp_festive_offers",
        campaign_name: "Festive Offers",
        platform: "tiktok",
        alert: "Comment volume increased by 3x",
        severity: "Warning",
        metric_impact: "Comments: 1.8K (+210%)",
        metric_trend: [500, 620, 800, 1100, 1400, 1650, 1800],
        action_label: "View",
        action_type: "inspect",
        status: "Investigating",
      },
      {
        id: "alt_004",
        time: "1 hour ago",
        timestamp: "2024-06-30T13:30:00Z",
        campaign_id: "cmp_retargeting_q2",
        campaign_name: "Retargeting – Q2",
        platform: "youtube",
        alert: "CPA increased by 40%",
        severity: "Critical",
        metric_impact: "CPA: $23.10 (+40%)",
        metric_trend: [16.5, 17.2, 18.1, 19.5, 21.0, 22.4, 23.1],
        action_label: "Take Action",
        action_type: "pause",
        status: "Open",
      },
      {
        id: "alt_005",
        time: "2 hours ago",
        timestamp: "2024-06-30T12:30:00Z",
        campaign_id: "cmp_new_product",
        campaign_name: "New Product Launch",
        platform: "meta",
        alert: "Mockery / meme comments increasing",
        severity: "Info",
        metric_impact: "Mockery: 14% (+60%)",
        metric_trend: [0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14],
        action_label: "View",
        action_type: "inspect",
        status: "Resolved",
      },
      {
        id: "alt_006",
        time: "3 hours ago",
        timestamp: "2024-06-30T11:30:00Z",
        campaign_id: "cmp_summer_2024",
        campaign_name: "Summer Collection 2024",
        platform: "meta",
        alert: "CTR drop detected",
        severity: "Warning",
        metric_impact: "CTR: 0.8% (-42%)",
        metric_trend: [1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8],
        action_label: "View",
        action_type: "inspect",
        status: "Open",
      },
      {
        id: "alt_007",
        time: "5 hours ago",
        timestamp: "2024-06-30T09:30:00Z",
        campaign_id: "cmp_monsoon_sale",
        campaign_name: "Monsoon Sale",
        platform: "google",
        alert: "Positive sentiment recovery",
        severity: "Info",
        metric_impact: "Pos. Ratio: 52% (+18%)",
        metric_trend: [0.44, 0.45, 0.47, 0.48, 0.50, 0.51, 0.52],
        action_label: "View",
        action_type: "inspect",
        status: "Resolved",
      },
      {
        id: "alt_008",
        time: "8 hours ago",
        timestamp: "2024-06-30T06:30:00Z",
        campaign_id: "cmp_festive_offers",
        campaign_name: "Festive Offers",
        platform: "tiktok",
        alert: "Spam comments detected",
        severity: "Warning",
        metric_impact: "Spam: 8% (+120%)",
        metric_trend: [0.03, 0.04, 0.05, 0.06, 0.07, 0.075, 0.08],
        action_label: "Take Action",
        action_type: "filter_comments",
        status: "Open",
      },
    ];
  }

  public getRecommendedActions(): RecommendedAction[] {
    return [
      {
        id: "rec_001",
        title: "Pause Campaign",
        description: "Audience fatigue is high. Consider pausing to prevent further spend.",
        button_label: "Pause",
        button_variant: "red",
        icon_name: "TrendingDown",
        campaign_id: "cmp_summer_2024",
        action_type: "pause",
      },
      {
        id: "rec_002",
        title: "Reduce Ad Frequency",
        description: "Lower frequency to 1.0 – 1.5 to reduce fatigue.",
        button_label: "Apply",
        button_variant: "orange",
        icon_name: "Sliders",
        campaign_id: "cmp_monsoon_sale",
        action_type: "frequency",
      },
      {
        id: "rec_003",
        title: "Switch Creative",
        description: "Try a new creative with different messaging.",
        button_label: "Create",
        button_variant: "blue",
        icon_name: "Layers",
        campaign_id: "cmp_summer_2024",
        action_type: "creative",
      },
      {
        id: "rec_004",
        title: "Adjust Audience",
        description: "Refine targeting to exclude fatigued audience segments.",
        button_label: "Update",
        button_variant: "green",
        icon_name: "Users",
        campaign_id: "cmp_new_product",
        action_type: "audience",
      },
      {
        id: "rec_005",
        title: "Enable Comment Filter",
        description: "Automatically hide spam and negative comments.",
        button_label: "Enable",
        button_variant: "purple",
        icon_name: "ShieldCheck",
        campaign_id: "cmp_festive_offers",
        action_type: "filter",
      },
    ];
  }

  public getAutomationRules(): AutomationRule[] {
    return [
      {
        id: "rule_001",
        title: "Auto-pause on critical risk (> 0.85)",
        description: "Pause campaign automatically",
        enabled: true,
        icon_name: "PauseCircle",
      },
      {
        id: "rule_002",
        title: "Reduce budget on negative sentiment spike",
        description: "Reduce daily budget by 30%",
        enabled: true,
        icon_name: "DollarSign",
      },
      {
        id: "rule_003",
        title: "Send Slack alert for warning",
        description: "Notify team on Slack",
        enabled: true,
        icon_name: "MessageSquare",
      },
      {
        id: "rule_004",
        title: "Auto-hide spam comments",
        description: "Hide comments with high spam score",
        enabled: false,
        icon_name: "ShieldAlert",
      },
    ];
  }

  public getSettings(): SettingsData {
    return {
      workspace: {
        name: "AdFatigue Radar",
        account_tier: "Demo Account",
        active_members: 5,
        alert_channels: 3,
        connected_integrations: 6,
        data_retention_months: 12,
        plan: "Pro",
      },
      profile: {
        account_name: "AdFatigue Radar",
        email: "demo@adfatigueradar.com",
        organization: "Demo Account",
        time_zone: "(GMT+5:30) Asia/Kolkata",
        language: "English",
      },
      notification_preferences: {
        in_app: { enabled: true, critical: true, warning: true, info: true },
        email: { enabled: true, critical: true, warning: true, info: true },
        slack: { enabled: true, critical: true, warning: true, info: true },
        webhooks: { enabled: false, critical: false, warning: false, info: false },
      },
      default_campaign_settings: {
        default_platform: "meta",
        default_audience_type: "Broad Audience",
        default_monitoring_duration_days: 30,
        default_alert_threshold: 0.65,
        currency: "USD ($)",
        frequency_cap: 1.5,
      },
      monitoring_rules: {
        audience_fatigue_risk: { warn_at: 0.65, critical_at: 0.85, current_value: 0.65, trend: [0.5, 0.54, 0.59, 0.62, 0.65] },
        sentiment_decay: { warn_at: 0.50, critical_at: 0.70, current_value: 0.50, trend: [0.38, 0.42, 0.46, 0.49, 0.50] },
        negative_comment_ratio: { warn_at: 0.30, critical_at: 0.50, current_value: 0.30, trend: [0.22, 0.25, 0.27, 0.29, 0.30] },
        cpa_increase: { warn_at: 0.40, critical_at: 0.80, current_value: 0.40, trend: [0.25, 0.29, 0.33, 0.37, 0.40] },
      },
      integrations: [
        { id: "int_meta", name: "Meta Ads", platform: "meta", connected: true, account_handle: "Kaladhar Royal" },
        { id: "int_google", name: "Google Ads", platform: "google", connected: true, account_handle: "student.dev@gmail.com" },
        { id: "int_tiktok", name: "TikTok Ads", platform: "tiktok", connected: false },
        { id: "int_youtube", name: "YouTube Ads", platform: "youtube", connected: true, account_handle: "Kaladhar Royal" },
        { id: "int_slack", name: "Slack", platform: "slack", connected: true, account_handle: "#ad-alerts" },
        { id: "int_webhook", name: "Webhook", platform: "webhook", connected: false },
      ],
      team_members: [
        { id: "tm_01", name: "Aditya Sharma", email: "aditya@adfatigueradar.com", role: "Owner", avatar_initials: "AD", access_level: "Full Access" },
        { id: "tm_02", name: "Priya Reddy", email: "priya@adfatigueradar.com", role: "Admin", avatar_initials: "PR", access_level: "Full Access" },
        { id: "tm_03", name: "Rohit Verma", email: "rohit@adfatigueradar.com", role: "Analyst", avatar_initials: "RV", access_level: "Analytics Only" },
        { id: "tm_04", name: "Neha Kapoor", email: "neha@adfatigueradar.com", role: "Analyst", avatar_initials: "NK", access_level: "Analytics Only" },
        { id: "tm_05", name: "Sai Kiran", email: "saikiran@adfatigueradar.com", role: "Viewer", avatar_initials: "SK", access_level: "Read Only" },
      ],
      data_privacy: {
        event_log_retention_months: 12,
        comment_data_retention_months: 6,
        anonymize_user_data: true,
        gdpr_compliance: true,
      },
    };
  }
}

export const devRepository = new DevRepository();
