"""Seed script to populate the Supabase PostgreSQL database with the demo dataset."""
from __future__ import annotations

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from backend.db.session import engine, database_configured


def seed_database() -> int:
    if not database_configured() or engine is None:
        print("[ERROR] DATABASE_URL is not configured.")
        return 1

    print("[INFO] Connecting to Supabase PostgreSQL...")

    # Use raw DBAPI connection to avoid SQLAlchemy interpreting JSON colons as bind params
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            # 1. Campaigns
            print("[INFO] Seeding campaigns...")
            cur.execute("""
                INSERT INTO campaigns
                (id, name, platform, status, pre_block_state, budget, created_at, metadata_json)
                VALUES
                (
                 'camp_meta_fatigue',
                 'Summer Creator Campaign',
                 'META',
                 'CRITICAL',
                 'ACTIVE',
                 15000,
                 '2026-09-17 10:00:00+05:30',
                 '{"channel":"Instagram","objective":"CONVERSIONS","currency":"INR","demo":true,"category":"Summer Apparel","target_audience":"18-34 Fashion Shoppers"}'
                ),
                (
                 'camp_meta_healthy',
                 'Product Launch Campaign',
                 'META',
                 'ACTIVE',
                 'ACTIVE',
                 25000,
                 '2026-09-22 10:00:00+05:30',
                 '{"channel":"Instagram","objective":"TRAFFIC","currency":"INR","demo":true,"category":"Product Launch","target_audience":"Broad Audience"}'
                ),
                (
                 'camp_tiktok_warning',
                 'Gen-Z Creator Campaign',
                 'TIKTOK',
                 'WARNING',
                 'ACTIVE',
                 12000,
                 '2026-09-20 10:00:00+05:30',
                 '{"channel":"TikTok","objective":"VIDEO_VIEWS","currency":"INR","demo":true,"category":"Creator UGC","target_audience":"16-24 Short Video Viewers"}'
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    platform = EXCLUDED.platform,
                    status = EXCLUDED.status,
                    pre_block_state = EXCLUDED.pre_block_state,
                    budget = EXCLUDED.budget,
                    created_at = EXCLUDED.created_at,
                    metadata_json = EXCLUDED.metadata_json;
            """)

            # 2. Ads
            print("[INFO] Seeding ads...")
            cur.execute("""
                INSERT INTO ads
                (id, campaign_id, metadata_json)
                VALUES
                (
                 'ad_meta_summer_01',
                 'camp_meta_fatigue',
                 '{"name":"Summer Creator Reel","format":"REEL","placement":"INSTAGRAM_REELS"}'
                ),
                (
                 'ad_meta_summer_02',
                 'camp_meta_fatigue',
                 '{"name":"Summer Product Carousel","format":"CAROUSEL","placement":"INSTAGRAM_FEED"}'
                ),
                (
                 'ad_meta_launch_01',
                 'camp_meta_healthy',
                 '{"name":"Product Launch Reel","format":"REEL","placement":"INSTAGRAM_REELS"}'
                ),
                (
                 'ad_tiktok_genz_01',
                 'camp_tiktok_warning',
                 '{"name":"Gen-Z Creator Video","format":"VIDEO","placement":"FOR_YOU"}'
                )
                ON CONFLICT (id) DO UPDATE SET
                    campaign_id = EXCLUDED.campaign_id,
                    metadata_json = EXCLUDED.metadata_json;
            """)

            # 3. Telemetry
            print("[INFO] Seeding telemetry...")
            cur.execute("""
                INSERT INTO telemetry
                (event_id, campaign_id, ad_id, timestamp, impressions, clicks, conversions, spend, reach, revenue)
                VALUES
                ('tel_001','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 10:00:00+05:30',5000,240,22,1920,4200,18700),
                ('tel_002','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 11:00:00+05:30',5100,230,20,1980,4250,17000),
                ('tel_003','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 12:00:00+05:30',5200,215,18,2040,4300,15300),
                ('tel_004','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 13:00:00+05:30',5300,195,16,2145,4350,13600),
                ('tel_005','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 14:00:00+05:30',5400,175,14,2275,4400,11900),
                ('tel_006','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 15:00:00+05:30',5500,155,12,2480,4450,10200),
                ('tel_007','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 16:00:00+05:30',5600,140,10,2660,4500,8500),
                ('tel_008','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 17:00:00+05:30',5700,125,9,2875,4520,7650),
                ('tel_009','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 18:00:00+05:30',5800,110,7,3080,4550,5950),
                ('tel_010','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 19:00:00+05:30',5900,95,6,3325,4580,5100),
                ('tel_011','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 20:00:00+05:30',6000,82,5,3608,4600,4250),
                ('tel_012','camp_meta_fatigue','ad_meta_summer_01','2026-09-30 21:00:00+05:30',6100,70,4,3850,4620,3400)
                ON CONFLICT (event_id) DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    conversions = EXCLUDED.conversions,
                    spend = EXCLUDED.spend,
                    reach = EXCLUDED.reach,
                    revenue = EXCLUDED.revenue;
            """)

            # 4. Comments
            print("[INFO] Seeding comments...")
            cur.execute("""
                INSERT INTO comments
                (comment_id, campaign_id, ad_id, timestamp, text, author_id_hmac)
                VALUES
                (
                 'comment_001',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 10:15:00+05:30',
                 'Love this product!',
                 'hmac_demo_001'
                ),
                (
                 'comment_002',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 11:20:00+05:30',
                 'This looks really good',
                 'hmac_demo_002'
                ),
                (
                 'comment_003',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 13:10:00+05:30',
                 'I have seen this ad several times already',
                 'hmac_demo_003'
                ),
                (
                 'comment_004',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 14:25:00+05:30',
                 'Stop showing me this ad again',
                 'hmac_demo_004'
                ),
                (
                 'comment_005',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 15:40:00+05:30',
                 'Why do I keep getting this advertisement?',
                 'hmac_demo_005'
                ),
                (
                 'comment_006',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 16:05:00+05:30',
                 'This ad is getting really annoying',
                 'hmac_demo_006'
                ),
                (
                 'comment_007',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 17:30:00+05:30',
                 'Not this ad again 🙄',
                 'hmac_demo_007'
                ),
                (
                 'comment_008',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 18:15:00+05:30',
                 'I have seen this like ten times already',
                 'hmac_demo_008'
                ),
                (
                 'comment_009',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 19:20:00+05:30',
                 'Please stop showing me this',
                 'hmac_demo_009'
                ),
                (
                 'comment_010',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 20:10:00+05:30',
                 'This campaign is getting repetitive',
                 'hmac_demo_010'
                ),
                (
                 'comment_011',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 21:05:00+05:30',
                 'Your product is too expensive',
                 'hmac_demo_011'
                ),
                (
                 'comment_012',
                 'camp_meta_fatigue',
                 'ad_meta_summer_01',
                 '2026-09-30 21:30:00+05:30',
                 'The ad is annoying and I keep seeing it',
                 'hmac_demo_012'
                )
                ON CONFLICT (comment_id) DO UPDATE SET
                    text = EXCLUDED.text,
                    author_id_hmac = EXCLUDED.author_id_hmac;
            """)

            # 5. NLP results
            print("[INFO] Seeding NLP results...")
            cur.execute("""
                INSERT INTO nlp_results
                (comment_id, category, confidence, sentiment, sentiment_score, critical_complaint)
                VALUES
                ('comment_001','GENERAL_POSITIVE',0.98,'POSITIVE',0.92,false),
                ('comment_002','GENERAL_POSITIVE',0.96,'POSITIVE',0.84,false),
                ('comment_003','AD_FATIGUE',0.94,'NEGATIVE',-0.72,false),
                ('comment_004','AD_FATIGUE',0.98,'NEGATIVE',-0.94,false),
                ('comment_005','AD_FATIGUE',0.96,'NEGATIVE',-0.88,false),
                ('comment_006','AD_FATIGUE',0.97,'NEGATIVE',-0.91,false),
                ('comment_007','AD_FATIGUE',0.98,'NEGATIVE',-0.95,false),
                ('comment_008','AD_FATIGUE',0.99,'NEGATIVE',-0.93,false),
                ('comment_009','AD_FATIGUE',0.97,'NEGATIVE',-0.92,false),
                ('comment_010','AD_FATIGUE',0.94,'NEGATIVE',-0.78,false),
                ('comment_011','PRICE_COMPLAINT',0.95,'NEGATIVE',-0.82,true),
                ('comment_012','AD_FATIGUE',0.99,'NEGATIVE',-0.96,false)
                ON CONFLICT (comment_id) DO UPDATE SET
                    category = EXCLUDED.category,
                    confidence = EXCLUDED.confidence,
                    sentiment = EXCLUDED.sentiment,
                    sentiment_score = EXCLUDED.sentiment_score,
                    critical_complaint = EXCLUDED.critical_complaint;
            """)

            # 6. Risk snapshots
            print("[INFO] Seeding risk snapshots...")
            cur.execute("""
                DELETE FROM risk_snapshots WHERE campaign_id IN ('camp_meta_fatigue', 'camp_meta_healthy', 'camp_tiktok_warning');

                INSERT INTO risk_snapshots
                (campaign_id, timestamp_simulated, audience_risk, economic_risk, state, severity, signals_json)
                VALUES
                (
                 'camp_meta_fatigue',
                 '2026-09-30 10:00:00+05:30',
                 18, 15, 'HEALTHY', 'LOW',
                 '{"ctr_change_pct":0,"cpc_change_pct":0,"negative_sentiment_pct":10,"sentiment_velocity":0.5}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 12:00:00+05:30',
                 32, 28, 'WATCH', 'MEDIUM',
                 '{"ctr_change_pct":-10,"cpc_change_pct":8,"negative_sentiment_pct":20,"sentiment_velocity":1.0}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 14:00:00+05:30',
                 48, 43, 'WATCH', 'MEDIUM',
                 '{"ctr_change_pct":-18,"cpc_change_pct":18,"negative_sentiment_pct":35,"sentiment_velocity":1.6}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 16:00:00+05:30',
                 67, 61, 'WARNING', 'HIGH',
                 '{"ctr_change_pct":-27,"cpc_change_pct":25,"negative_sentiment_pct":52,"sentiment_velocity":2.7}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 18:00:00+05:30',
                 78, 73, 'WARNING', 'HIGH',
                 '{"ctr_change_pct":-34,"cpc_change_pct":31,"negative_sentiment_pct":68,"sentiment_velocity":3.6}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 20:00:00+05:30',
                 87, 82, 'CRITICAL', 'CRITICAL',
                 '{"ctr_change_pct":-42,"cpc_change_pct":39,"negative_sentiment_pct":76,"sentiment_velocity":4.5}'
                ),
                (
                 'camp_meta_fatigue',
                 '2026-09-30 21:00:00+05:30',
                 91, 88, 'CRITICAL', 'CRITICAL',
                 '{"ctr_change_pct":-46,"cpc_change_pct":45,"negative_sentiment_pct":83,"sentiment_velocity":5.1}'
                ),
                (
                 'camp_meta_healthy',
                 '2026-09-30 21:00:00+05:30',
                 12, 10, 'HEALTHY', 'LOW',
                 '{"ctr_change_pct":2,"cpc_change_pct":-4,"negative_sentiment_pct":5,"sentiment_velocity":0.2}'
                ),
                (
                 'camp_tiktok_warning',
                 '2026-09-30 21:00:00+05:30',
                 58, 52, 'WARNING', 'HIGH',
                 '{"ctr_change_pct":-20,"cpc_change_pct":18,"negative_sentiment_pct":42,"sentiment_velocity":2.1}'
                );
            """)

            # 7. Actions
            print("[INFO] Seeding actions...")
            cur.execute("""
                INSERT INTO actions
                (id, campaign_id, timestamp_simulated, action, previous_state, new_state, result_json)
                VALUES
                (
                 'action_001',
                 'camp_meta_fatigue',
                 '2026-09-30 20:05:00+05:30',
                 'CREATE_ALERT',
                 'WARNING',
                 'CRITICAL',
                 '{"success":true,"fatigue_score":87,"reason":"Critical fatigue threshold crossed"}'
                ),
                (
                 'action_002',
                 'camp_meta_fatigue',
                 '2026-09-30 20:10:00+05:30',
                 'SIMULATED_PAUSE',
                 'ACTIVE',
                 'PAUSED',
                 '{"success":true,"simulation":true,"guardrail_passed":true,"confidence":0.96}'
                )
                ON CONFLICT (id) DO UPDATE SET
                    action = EXCLUDED.action,
                    previous_state = EXCLUDED.previous_state,
                    new_state = EXCLUDED.new_state,
                    result_json = EXCLUDED.result_json;
            """)

            # 8. Audit log
            print("[INFO] Seeding audit log events...")
            cur.execute("""
                INSERT INTO audit_events
                (
                 campaign_id,
                 audit_id,
                 timestamp_simulated,
                 actor_type,
                 action,
                 previous_state,
                 new_state,
                 reason_codes,
                 risk_json,
                 readback_verified,
                 config_version,
                 confidence,
                 log_hash
                )
                VALUES
                (
                 'camp_meta_fatigue',
                 'AUDIT001',
                 '2026-09-30 19:55:00+05:30',
                 'SYSTEM',
                 'SENTIMENT_ANALYSIS',
                 'ACTIVE',
                 'ACTIVE',
                 '["NEGATIVE_SENTIMENT_SPIKE"]',
                 '{"negative_sentiment":83,"velocity":5.1}',
                 true,
                 'demo-v1',
                 0.96,
                 'demo_hash_001'
                ),
                (
                 'camp_meta_fatigue',
                 'AUDIT002',
                 '2026-09-30 20:00:00+05:30',
                 'SYSTEM',
                 'RISK_THRESHOLD_CROSSED',
                 'WARNING',
                 'CRITICAL',
                 '["CTR_DECLINE","CPC_INCREASE","NEGATIVE_SENTIMENT","VELOCITY_SPIKE"]',
                 '{"fatigue_score":87,"audience_risk":91,"economic_risk":88}',
                 true,
                 'demo-v1',
                 0.95,
                 'demo_hash_002'
                ),
                (
                 'camp_meta_fatigue',
                 'AUDIT003',
                 '2026-09-30 20:05:00+05:30',
                 'SYSTEM',
                 'CREATE_ALERT',
                 'CRITICAL',
                 'CRITICAL',
                 '["FATIGUE_SCORE_ABOVE_THRESHOLD"]',
                 '{"fatigue_score":87}',
                 true,
                 'demo-v1',
                 0.97,
                 'demo_hash_003'
                ),
                (
                 'camp_meta_fatigue',
                 'AUDIT004',
                 '2026-09-30 20:10:00+05:30',
                 'AUTOMATION',
                 'SIMULATED_PAUSE',
                 'ACTIVE',
                 'PAUSED',
                 '["CRITICAL_FATIGUE","GUARDRAIL_PASSED"]',
                 '{"fatigue_score":87,"confidence":0.96}',
                 true,
                 'demo-v1',
                 0.96,
                 'demo_hash_004'
                ),
                (
                 'camp_meta_fatigue',
                 'AUDIT005',
                 '2026-09-30 20:11:00+05:30',
                 'SYSTEM',
                 'SLACK_NOTIFICATION',
                 'PAUSED',
                 'PAUSED',
                 '["CRITICAL_ALERT"]',
                 '{"notification":"sent"}',
                 true,
                 'demo-v1',
                 0.99,
                 'demo_hash_005'
                )
                ON CONFLICT (campaign_id, audit_id) DO UPDATE SET
                    timestamp_simulated = EXCLUDED.timestamp_simulated,
                    action = EXCLUDED.action,
                    previous_state = EXCLUDED.previous_state,
                    new_state = EXCLUDED.new_state,
                    reason_codes = EXCLUDED.reason_codes,
                    risk_json = EXCLUDED.risk_json,
                    confidence = EXCLUDED.confidence;
            """)

            # 9. Threshold overrides
            print("[INFO] Seeding threshold overrides...")
            cur.execute("""
                DELETE FROM threshold_overrides WHERE campaign_id = 'camp_meta_fatigue';

                INSERT INTO threshold_overrides
                (campaign_id, overrides_json, config_version, updated_at)
                VALUES
                (
                 'camp_meta_fatigue',
                 '{
                   "fatigue_warning":60,
                   "fatigue_critical":80,
                   "negative_sentiment":60,
                   "ctr_drop_pct":20,
                   "cpc_increase_pct":25,
                   "cpm_increase_pct":20,
                   "minimum_confidence":0.90,
                   "sentiment_velocity_threshold":2.5
                 }',
                 'demo-v1',
                 '2026-09-30 20:00:00+05:30'
                );
            """)

            # 10. Automation rules
            print("[INFO] Seeding automation rules...")
            cur.execute("""
                INSERT INTO automation_rules
                (id, title, enabled, settings_json)
                VALUES
                (
                 'rule_critical_fatigue',
                 'Critical Ad Fatigue Protection',
                 true,
                 '{
                   "fatigue_score_min":80,
                   "confidence_min":0.90,
                   "action":"SIMULATED_PAUSE",
                   "require_guardrail":true,
                   "simulation_mode":true
                 }'
                )
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    enabled = EXCLUDED.enabled,
                    settings_json = EXCLUDED.settings_json;
            """)

            # 11. Workspace settings
            print("[INFO] Seeding workspace settings...")
            cur.execute("""
                INSERT INTO workspace_settings
                (id, settings_json)
                VALUES
                (
                 'workspace_demo',
                 '{
                   "workspace_name":"AdFatigueRadar Demo",
                   "timezone":"Asia/Kolkata",
                   "currency":"INR",
                   "simulation_mode":true,
                   "auto_pause_enabled":false,
                   "minimum_confidence":0.90,
                   "polling_interval_seconds":60,
                   "notifications":{
                      "slack":true,
                      "email":false
                   }
                 }'
                ),
                (
                 'workspace',
                 '{
                   "workspace_name":"AdFatigueRadar Demo",
                   "timezone":"Asia/Kolkata",
                   "currency":"INR",
                   "simulation_mode":true,
                   "auto_pause_enabled":false,
                   "minimum_confidence":0.90,
                   "polling_interval_seconds":60,
                   "notifications":{
                      "slack":true,
                      "email":false
                   }
                 }'
                )
                ON CONFLICT (id) DO UPDATE SET
                    settings_json = EXCLUDED.settings_json;
            """)

            # 12. Replay session
            print("[INFO] Seeding replay session...")
            cur.execute("""
                INSERT INTO replay_sessions
                (id, campaign_id, seed, speed, config_json, started_at_simulated, reset_at_simulated, status)
                VALUES
                (
                 'replay_demo_001',
                 'camp_meta_fatigue',
                 42,
                 1.0,
                 '{"demo":true,"objective":"Simulate 12-hour ad fatigue degradation"}',
                 '2026-09-30 10:00:00+05:30',
                 NULL,
                 'COMPLETED'
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    config_json = EXCLUDED.config_json;
            """)

        raw_conn.commit()
        print("[SUCCESS] All demo seed records successfully inserted into Supabase PostgreSQL!")
        return 0
    except Exception as e:
        raw_conn.rollback()
        print(f"[ERROR] Failed to seed database: {e}")
        return 1
    finally:
        raw_conn.close()


if __name__ == "__main__":
    sys.exit(seed_database())
