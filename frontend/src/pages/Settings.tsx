import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  LayoutGrid,
  Users,
  Bell,
  Link2,
  Shield,
  Crown,
  CheckCircle2,
  Lock,
  Trash2,
  Download,
  Loader2,
  ChevronDown,
  MoreHorizontal,
  Mail,
  Sliders,
} from "lucide-react";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { Sparkline } from "../components/common/Sparkline";
import { useSettings, useUpdateSettings } from "../hooks/useSettings";
import { SettingsData } from "../types/contracts";

const profileSchema = z.object({
  account_name: z.string().min(2),
  email: z.string().email(),
  organization: z.string().min(2),
  time_zone: z.string(),
  language: z.string(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState("general");
  const [savedSuccess, setSavedSuccess] = useState(false);

  const { data: settings, isLoading } = useSettings();
  const updateSettingsMutation = useUpdateSettings();

  const [notificationState, setNotificationState] = useState({
    in_app: { enabled: true, critical: true, warning: true, info: true },
    email: { enabled: true, critical: true, warning: true, info: true },
    slack: { enabled: true, critical: true, warning: true, info: true },
    webhooks: { enabled: false, critical: false, warning: false, info: false },
  });

  const [privacyState, setPrivacyState] = useState({
    anonymize: true,
    gdpr: true,
  });

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: {
      account_name: settings?.profile.account_name || "AdFatigue Radar",
      email: settings?.profile.email || "demo@adfatigueradar.com",
      organization: settings?.profile.organization || "Demo Account",
      time_zone: settings?.profile.time_zone || "(GMT+5:30) Asia/Kolkata",
      language: settings?.profile.language || "English",
    },
  });

  if (isLoading || !settings) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-400 text-sm animate-pulse">Loading workspace settings...</div>
      </div>
    );
  }

  const onSubmitProfile = async (data: ProfileFormValues) => {
    try {
      await updateSettingsMutation.mutateAsync({
        profile: data,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Toast */}
      {savedSuccess && (
        <div className="fixed top-20 right-8 z-50 bg-[#1E3A2B] text-white px-4 py-3 rounded-2xl shadow-xl flex items-center gap-3 border border-emerald-600 animate-in slide-in-from-top">
          <CheckCircle2 className="w-5 h-5 text-[#34D399]" />
          <span className="text-xs font-semibold">Settings updated and saved successfully.</span>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Settings</h1>
        <p className="text-sm text-[#6B7280] mt-1">
          Customize your workspace, configure monitoring rules, and manage integrations.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-[#E5E7EB] text-sm font-medium overflow-x-auto">
        {[
          { id: "general", label: "General" },
          { id: "campaigns", label: "Campaigns" },
          { id: "monitoring", label: "Monitoring & Alerts" },
          { id: "integrations", label: "Integrations" },
          { id: "team", label: "Users & Team" },
          { id: "billing", label: "Billing" },
          { id: "privacy", label: "Data & Privacy" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pb-3 relative transition-colors cursor-pointer whitespace-nowrap ${
              activeTab === tab.id
                ? "text-[#E85D35] font-semibold"
                : "text-[#6B7280] hover:text-[#111827]"
            }`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#E85D35] rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Top 6 Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <LayoutGrid className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Workspace</div>
            <div className="text-xs font-bold text-slate-900 truncate">AdFatigue Radar</div>
            <div className="text-[10px] text-slate-500">Demo Account</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Users</div>
            <div className="text-sm font-bold text-slate-900">5</div>
            <div className="text-[10px] text-slate-500">Active Members</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-red-50 text-red-600 flex items-center justify-center shrink-0">
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Alert Channels</div>
            <div className="text-sm font-bold text-slate-900">3</div>
            <div className="text-[10px] text-slate-500">Configured</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <Link2 className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Integrations</div>
            <div className="text-sm font-bold text-slate-900">6</div>
            <div className="text-[10px] text-slate-500">Connected</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Data Retention</div>
            <div className="text-xs font-bold text-slate-900">12 months</div>
            <div className="text-[10px] text-slate-500">Event Logs</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3.5 border border-[#EAECEF] card-subtle-shadow flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center shrink-0">
            <Crown className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-semibold">Plan</div>
            <div className="text-xs font-bold text-slate-900">Pro</div>
            <div className="text-[10px] text-[#E85D35] font-semibold cursor-pointer hover:underline">Manage Plan</div>
          </div>
        </div>
      </div>

      {/* Row 1: Profile & Organization (Left) + Notification Preferences (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile & Organization */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Profile & Organization</h3>
              <p className="text-[11px] text-slate-400">Manage your account details and organization settings.</p>
            </div>
            <button
              onClick={handleSubmit(onSubmitProfile)}
              disabled={isSubmitting}
              className="px-3 py-1.5 rounded-xl bg-[#E4EFE3] hover:bg-[#D4E4D3] text-[#1E3A2B] text-xs font-semibold cursor-pointer transition-colors"
            >
              Save Changes
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmitProfile)} className="space-y-3.5">
            <div className="flex items-center gap-4 mb-2">
              <div className="w-12 h-12 rounded-full bg-[#B45309] text-white flex items-center justify-center font-bold text-sm">
                AD
              </div>
              <button
                type="button"
                className="px-3 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Change Photo
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Account Name</label>
                <input
                  {...register("account_name")}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-700"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                <input
                  {...register("email")}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-700"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Organization</label>
                <input
                  {...register("organization")}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-700"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Time Zone</label>
                <select
                  {...register("time_zone")}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-700"
                >
                  <option>(GMT+5:30) Asia/Kolkata</option>
                  <option>(GMT+0:00) UTC</option>
                  <option>(GMT-5:00) America/New_York</option>
                  <option>(GMT-8:00) America/Los_Angeles</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Language</label>
              <select
                {...register("language")}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-700"
              >
                <option>English</option>
                <option>Spanish</option>
                <option>German</option>
              </select>
            </div>
          </form>
        </div>

        {/* Notification Preferences */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Notification Preferences</h3>
              <p className="text-[11px] text-slate-400">Choose how and when you want to be notified about important events.</p>
            </div>
            <button className="px-3 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50">
              Test Notification
            </button>
          </div>

          <div className="space-y-4">
            {/* Severity header */}
            <div className="flex items-center justify-end gap-6 text-[10px] text-slate-400 font-bold uppercase pr-2">
              <span>Severity</span>
            </div>

            {/* In-App */}
            <div className="flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center shrink-0">
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-slate-900">In-App Notifications</div>
                  <div className="text-[10px] text-slate-400">Get notified within the platform</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 text-[11px] font-medium text-slate-700">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-red-600" />
                    <span>Critical</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-amber-500" />
                    <span>Warning</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-blue-500" />
                    <span>Info</span>
                  </label>
                </div>
                <button
                  onClick={() =>
                    setNotificationState((prev) => ({
                      ...prev,
                      in_app: { ...prev.in_app, enabled: !prev.in_app.enabled },
                    }))
                  }
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    notificationState.in_app.enabled ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${notificationState.in_app.enabled ? "translate-x-4" : ""}`} />
                </button>
              </div>
            </div>

            {/* Email */}
            <div className="flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-slate-900">Email Alerts</div>
                  <div className="text-[10px] text-slate-400">Receive alerts via email</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 text-[11px] font-medium text-slate-700">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-red-600" />
                    <span>Critical</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-amber-500" />
                    <span>Warning</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-blue-500" />
                    <span>Info</span>
                  </label>
                </div>
                <button
                  onClick={() =>
                    setNotificationState((prev) => ({
                      ...prev,
                      email: { ...prev.email, enabled: !prev.email.enabled },
                    }))
                  }
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    notificationState.email.enabled ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${notificationState.email.enabled ? "translate-x-4" : ""}`} />
                </button>
              </div>
            </div>

            {/* Slack */}
            <div className="flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                  <PlatformIcon platform="slack" size={16} />
                </div>
                <div>
                  <div className="font-bold text-slate-900">Slack Integration</div>
                  <div className="text-[10px] text-slate-400">Send alerts to Slack channels</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 text-[11px] font-medium text-slate-700">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-red-600" />
                    <span>Critical</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-amber-500" />
                    <span>Warning</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-blue-500" />
                    <span>Info</span>
                  </label>
                </div>
                <button
                  onClick={() =>
                    setNotificationState((prev) => ({
                      ...prev,
                      slack: { ...prev.slack, enabled: !prev.slack.enabled },
                    }))
                  }
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    notificationState.slack.enabled ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${notificationState.slack.enabled ? "translate-x-4" : ""}`} />
                </button>
              </div>
            </div>

            {/* Webhooks */}
            <div className="flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center shrink-0">
                  <Sliders className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-slate-900">Webhooks</div>
                  <div className="text-[10px] text-slate-400">Send real-time alerts to your system</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 text-[11px] font-medium text-slate-400">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" className="rounded" />
                    <span>Critical</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" className="rounded" />
                    <span>Warning</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input type="checkbox" className="rounded" />
                    <span>Info</span>
                  </label>
                </div>
                <button
                  onClick={() =>
                    setNotificationState((prev) => ({
                      ...prev,
                      webhooks: { ...prev.webhooks, enabled: !prev.webhooks.enabled },
                    }))
                  }
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    notificationState.webhooks.enabled ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${notificationState.webhooks.enabled ? "translate-x-4" : ""}`} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Default Campaign Settings (Left) + Monitoring & Alert Rules (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Default Campaign Settings */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Default Campaign Settings</h3>
              <p className="text-[11px] text-slate-400">These settings will be applied when creating new campaigns.</p>
            </div>
            <button className="px-3 py-1.5 rounded-xl bg-[#E4EFE3] hover:bg-[#D4E4D3] text-[#1E3A2B] text-xs font-semibold cursor-pointer">
              Save Changes
            </button>
          </div>

          <div className="space-y-3.5">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Default Platform</label>
                <select className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                  <option>Meta Ads</option>
                  <option>Google Ads</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Default Audience Type</label>
                <select className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                  <option>Broad Audience</option>
                  <option>Lookalike</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Monitoring Duration</label>
                <select className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                  <option>30 Days</option>
                  <option>60 Days</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Alert Threshold (Risk)</label>
                <select className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                  <option>0.65 (Warning)</option>
                  <option>0.75 (Soft Reduced)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
                <select className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                  <option>USD ($)</option>
                  <option>EUR (€)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Frequency Cap</label>
                <input
                  type="number"
                  defaultValue={1.5}
                  step={0.1}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Monitoring & Alert Rules (Threshold Cards) */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Monitoring & Alert Rules</h3>
              <p className="text-[11px] text-slate-400">Configure global thresholds and automation preferences.</p>
            </div>
            <button className="px-3 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50">
              Edit Rules
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {/* Audience Fatigue Risk */}
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block truncate">Audience Fatigue Risk</span>
              <div className="text-lg font-bold text-[#EA580C] my-1">0.65</div>
              <Sparkline data={[0.5, 0.54, 0.59, 0.62, 0.65]} color="#EA580C" width={55} height={14} />
              <div className="mt-2 space-y-0.5 text-[9px] text-slate-500">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  <span>Warn at 0.65</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  <span>Critical at 0.85</span>
                </div>
              </div>
            </div>

            {/* Sentiment Decay */}
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block truncate">Sentiment Decay</span>
              <div className="text-lg font-bold text-[#EF4444] my-1">0.50</div>
              <Sparkline data={[0.38, 0.42, 0.46, 0.49, 0.5]} color="#EF4444" width={55} height={14} />
              <div className="mt-2 space-y-0.5 text-[9px] text-slate-500">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  <span>Warn at 0.50</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  <span>Critical at 0.70</span>
                </div>
              </div>
            </div>

            {/* Negative Comment Ratio */}
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block truncate">Negative Ratio</span>
              <div className="text-lg font-bold text-[#EF4444] my-1">0.30</div>
              <Sparkline data={[0.22, 0.25, 0.27, 0.29, 0.3]} color="#EF4444" width={55} height={14} />
              <div className="mt-2 space-y-0.5 text-[9px] text-slate-500">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  <span>Warn at 0.30</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  <span>Critical at 0.50</span>
                </div>
              </div>
            </div>

            {/* CPA Increase */}
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block truncate">CPA Increase</span>
              <div className="text-lg font-bold text-[#EA580C] my-1">40%</div>
              <Sparkline data={[0.25, 0.29, 0.33, 0.37, 0.4]} color="#EA580C" width={55} height={14} />
              <div className="mt-2 space-y-0.5 text-[9px] text-slate-500">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  <span>Warn at 40%</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  <span>Critical at 80%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Integrations (Left) + Team Members (Middle) + Data & Privacy (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Integrations */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Integrations</h3>
                <p className="text-[11px] text-slate-400">Connect your ad accounts and external tools.</p>
              </div>
              <button className="px-2.5 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                Manage
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              {settings.integrations.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex items-center gap-2 min-w-0">
                    <PlatformIcon platform={item.platform} size={16} />
                    <div>
                      <span className="font-bold text-slate-900 block">{item.name}</span>
                      {item.account_handle && (
                        <span className="text-[10px] text-slate-400 truncate">{item.account_handle}</span>
                      )}
                    </div>
                  </div>

                  {item.connected ? (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                      Connected
                    </span>
                  ) : (
                    <button className="px-2.5 py-1 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 text-[10px] font-bold">
                      Connect
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Team Members</h3>
                <p className="text-[11px] text-slate-400">Manage team access and permissions.</p>
              </div>
              <button className="px-2.5 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                Invite Member
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              {settings.team_members.map((mem) => (
                <div key={mem.id} className="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-slate-300 text-slate-800 font-bold text-[10px] flex items-center justify-center">
                      {mem.avatar_initials}
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">{mem.name}</div>
                      <div className="text-[10px] text-slate-400">{mem.role}</div>
                    </div>
                  </div>

                  <select
                    defaultValue={mem.access_level}
                    className="text-[10px] font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg px-2 py-1"
                  >
                    <option>Full Access</option>
                    <option>Analytics Only</option>
                    <option>Read Only</option>
                  </select>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Data & Privacy */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Data & Privacy</h3>
                <p className="text-[11px] text-slate-400">Manage data retention and privacy settings.</p>
              </div>
              <button className="px-2.5 py-1 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                View Policy
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-700">Event Log Retention</span>
                <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-semibold">
                  <option>12 Months</option>
                  <option>24 Months</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-700">Comment Data Retention</span>
                <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-semibold">
                  <option>6 Months</option>
                  <option>12 Months</option>
                </select>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div>
                  <span className="font-bold text-slate-800 block">Anonymize User Data</span>
                  <span className="text-[10px] text-slate-400">Hide user identifiers in comments</span>
                </div>
                <button
                  onClick={() => setPrivacyState((p) => ({ ...p, anonymize: !p.anonymize }))}
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    privacyState.anonymize ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${privacyState.anonymize ? "translate-x-4" : ""}`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">GDPR Compliance</span>
                  <span className="text-[10px] text-slate-400">Enable data handling controls</span>
                </div>
                <button
                  onClick={() => setPrivacyState((p) => ({ ...p, gdpr: !p.gdpr }))}
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer ${
                    privacyState.gdpr ? "bg-[#10B981]" : "bg-slate-300"
                  }`}
                >
                  <div className={`bg-white w-4 h-4 rounded-full shadow-sm transform ${privacyState.gdpr ? "translate-x-4" : ""}`} />
                </button>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="font-bold text-slate-800">Export My Data</span>
                <button className="px-3 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-slate-700 text-xs">
                  Export
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="font-bold text-[#DC2626]">Delete Account</span>
                <button className="px-3 py-1 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 font-bold text-xs">
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
