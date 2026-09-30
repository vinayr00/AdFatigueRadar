import React, { useState, useMemo } from "react";
import {
  AlertTriangle,
  Zap,
  CheckCircle2,
  Info,
  TrendingDown,
  Sliders,
  Layers,
  Users,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Search,
  Loader2,
  PauseCircle,
  DollarSign,
  MessageSquare,
  ShieldAlert,
  ChevronRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { KPICard } from "../components/common/KPICard";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { Sparkline } from "../components/common/Sparkline";
import { useAlerts, useRecommendedActions, useAutomationRules, useToggleAutomationRule, useExecuteAction } from "../hooks/useAlerts";
import { AlertItem, RecommendedAction } from "../types/contracts";

export const AlertsActions: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"all" | "history" | "rules" | "escalations">("all");
  const [campaignFilter, setCampaignFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const { data: alerts = [], isLoading: alertsLoading } = useAlerts();
  const { data: recommendations = [] } = useRecommendedActions();
  const { data: rules = [] } = useAutomationRules();
  const toggleRuleMutation = useToggleAutomationRule();
  const executeActionMutation = useExecuteAction();

  // Summary counts
  const totalAlerts = alerts.length;
  const criticalCount = alerts.filter((a) => a.severity === "Critical").length;
  const warningCount = alerts.filter((a) => a.severity === "Warning").length;
  const infoCount = alerts.filter((a) => a.severity === "Info").length;

  const filteredAlerts = useMemo(() => {
    return alerts.filter((item) => {
      if (campaignFilter !== "all" && item.campaign_id !== campaignFilter && item.campaign_name !== campaignFilter) return false;
      if (platformFilter !== "all" && item.platform.toLowerCase() !== platformFilter.toLowerCase()) return false;
      if (severityFilter !== "all" && item.severity.toLowerCase() !== severityFilter.toLowerCase()) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return item.alert.toLowerCase().includes(q) || item.campaign_name.toLowerCase().includes(q);
      }
      return true;
    });
  }, [alerts, campaignFilter, platformFilter, severityFilter, searchQuery]);

  // Alert Trends Stacked Bar Data
  const trendData = [
    { day: "Jun 24", Critical: 2, Warning: 3, Info: 2, Resolved: 1 },
    { day: "Jun 25", Critical: 3, Warning: 2, Info: 1, Resolved: 2 },
    { day: "Jun 26", Critical: 1, Warning: 4, Info: 2, Resolved: 3 },
    { day: "Jun 27", Critical: 4, Warning: 3, Info: 1, Resolved: 2 },
    { day: "Jun 28", Critical: 2, Warning: 5, Info: 3, Resolved: 4 },
    { day: "Jun 29", Critical: 3, Warning: 2, Info: 2, Resolved: 3 },
    { day: "Jun 30", Critical: 2, Warning: 3, Info: 1, Resolved: 2 },
  ];

  // Alert Sources Donut Data
  const sourceDonut = [
    { name: "Audience Signals", value: 42, color: "#10B981" },
    { name: "Comment Analysis", value: 28, color: "#F59E0B" },
    { name: "Performance Metrics", value: 15, color: "#3B82F6" },
    { name: "Platform API", value: 10, color: "#8B5CF6" },
    { name: "System Monitoring", value: 5, color: "#EF4444" },
  ];

  const handleExecute = async (actionId: string, actionType: string) => {
    try {
      const res = await executeActionMutation.mutateAsync({ actionId, actionType });
      setActionSuccessMsg(res.message);
      setTimeout(() => setActionSuccessMsg(null), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  const getButtonVariantStyles = (variant: string) => {
    switch (variant) {
      case "red":
        return "bg-[#EF4444] hover:bg-[#DC2626] text-white";
      case "orange":
        return "bg-[#F59E0B] hover:bg-[#D97706] text-white";
      case "blue":
        return "bg-[#3B82F6] hover:bg-[#2563EB] text-white";
      case "green":
        return "bg-[#10B981] hover:bg-[#059669] text-white";
      case "purple":
        return "bg-[#8B5CF6] hover:bg-[#7C3AED] text-white";
      default:
        return "bg-slate-800 hover:bg-slate-900 text-white";
    }
  };

  const getActionIcon = (iconName: string) => {
    switch (iconName) {
      case "TrendingDown":
        return <TrendingDown className="w-5 h-5 text-[#EF4444]" />;
      case "Sliders":
        return <Sliders className="w-5 h-5 text-[#F59E0B]" />;
      case "Layers":
        return <Layers className="w-5 h-5 text-[#3B82F6]" />;
      case "Users":
        return <Users className="w-5 h-5 text-[#10B981]" />;
      case "ShieldCheck":
        return <ShieldCheck className="w-5 h-5 text-[#8B5CF6]" />;
      default:
        return <Sparkles className="w-5 h-5 text-emerald-600" />;
    }
  };

  const getAutomationIcon = (iconName: string) => {
    switch (iconName) {
      case "PauseCircle":
        return <PauseCircle className="w-5 h-5 text-[#EF4444]" />;
      case "DollarSign":
        return <DollarSign className="w-5 h-5 text-[#F59E0B]" />;
      case "MessageSquare":
        return <MessageSquare className="w-5 h-5 text-[#10B981]" />;
      case "ShieldAlert":
        return <ShieldAlert className="w-5 h-5 text-[#8B5CF6]" />;
      default:
        return <Zap className="w-5 h-5 text-indigo-500" />;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Toast Feedback */}
      {actionSuccessMsg && (
        <div className="fixed top-20 right-8 z-50 bg-[#1E3A2B] text-white px-4 py-3 rounded-2xl shadow-xl flex items-center gap-3 border border-emerald-600 animate-in slide-in-from-top duration-300">
          <CheckCircle2 className="w-5 h-5 text-[#34D399]" />
          <span className="text-xs font-semibold">{actionSuccessMsg}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Alerts & Actions</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Stay ahead with real-time alerts, AI-driven insights, and automated actions to protect your ad performance.
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E8F0] rounded-2xl text-xs font-semibold text-slate-700 shadow-xs self-start sm:self-auto">
          <span>📅 Last 7 Days ˅</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-[#E5E7EB] text-sm font-medium">
        {[
          { id: "all", label: "All Alerts" },
          { id: "history", label: "Action History" },
          { id: "rules", label: "Automation Rules" },
          { id: "escalations", label: "Escalations" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`pb-3 relative transition-colors cursor-pointer ${
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

      {/* 5 Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KPICard
          title="Total Alerts"
          value={totalAlerts}
          icon={<AlertTriangle className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
          sparklineData={[10, 12, 11, 14, 13, 12]}
          sparklineColor="#EF4444"
        />
        <KPICard
          title="Critical"
          value={criticalCount}
          change="+25%"
          isPositive={false}
          icon={<Zap className="w-5 h-5 text-[#F59E0B]" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={[3, 4, 4, 5, 5, 5]}
          sparklineColor="#F59E0B"
        />
        <KPICard
          title="Warning"
          value={warningCount}
          change="+33%"
          isPositive={false}
          icon={<AlertTriangle className="w-5 h-5 text-[#F59E0B]" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={[2, 3, 3, 4, 4, 4]}
          sparklineColor="#F59E0B"
        />
        <KPICard
          title="Info"
          value={infoCount}
          change="-33%"
          isPositive={true}
          icon={<Info className="w-5 h-5 text-[#3B82F6]" />}
          iconBg="bg-[#DBEAFE]"
          sparklineData={[4, 3, 3, 2, 2, 2]}
          sparklineColor="#3B82F6"
        />
        <KPICard
          title="Auto Actions"
          value={8}
          change="+60%"
          isPositive={true}
          icon={<Sparkles className="w-5 h-5 text-[#8B5CF6]" />}
          iconBg="bg-[#EDE9FE]"
          sparklineData={[3, 5, 6, 7, 8, 8]}
          sparklineColor="#8B5CF6"
        />
      </div>

      {/* Main Grid: Alerts Table (Left 2 cols) + Recommendations & Automation (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recent Alerts Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl p-3 border border-[#EAECEF] card-subtle-shadow flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-bold text-slate-900 text-sm pl-1">Recent Alerts</h3>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={campaignFilter}
                onChange={(e) => setCampaignFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
              >
                <option value="all">All Campaigns</option>
                <option value="cmp_summer_2024">Summer Collection 2024</option>
                <option value="cmp_monsoon_sale">Monsoon Sale</option>
                <option value="cmp_festive_offers">Festive Offers</option>
              </select>

              <select
                value={platformFilter}
                onChange={(e) => setPlatformFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
              >
                <option value="all">All Platforms</option>
                <option value="meta">Meta Ads</option>
                <option value="google">Google Ads</option>
                <option value="tiktok">TikTok Ads</option>
                <option value="youtube">YouTube Ads</option>
              </select>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>

              <div className="relative min-w-[140px]">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search alerts..."
                  className="w-full pl-8 pr-2.5 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-[#EAECEF] card-subtle-shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-[#FAFBF9] border-b border-[#EAECEF] text-slate-400 uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="p-3 w-8"><input type="checkbox" className="rounded" /></th>
                    <th className="p-3">Time</th>
                    <th className="p-3">Campaign</th>
                    <th className="p-3">Alert</th>
                    <th className="p-3">Severity</th>
                    <th className="p-3">Metric Impact</th>
                    <th className="p-3 text-center">Action</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F3F5]">
                  {alertsLoading ? (
                    <tr>
                      <td colSpan={8} className="text-center py-8 text-slate-400">Loading alerts stream...</td>
                    </tr>
                  ) : filteredAlerts.map((item) => (
                    <tr key={item.id} className="hover:bg-[#F9FAF8] transition-colors">
                      <td className="p-3"><input type="checkbox" className="rounded" /></td>
                      <td className="p-3 font-medium text-slate-500 whitespace-nowrap">{item.time}</td>
                      <td className="p-3 font-semibold text-slate-900">
                        <div className="flex items-center gap-2">
                          <PlatformIcon platform={item.platform} size={16} />
                          <span className="truncate max-w-[140px]">{item.campaign_name}</span>
                        </div>
                      </td>
                      <td className="p-3 text-slate-700 font-medium max-w-[200px]">{item.alert}</td>
                      <td className="p-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            item.severity === "Critical"
                              ? "bg-red-100 text-red-700 border border-red-200"
                              : item.severity === "Warning"
                              ? "bg-amber-100 text-amber-800 border border-amber-200"
                              : "bg-blue-100 text-blue-700 border border-blue-200"
                          }`}
                        >
                          {item.severity}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-semibold text-slate-800 whitespace-nowrap">
                            {item.metric_impact}
                          </span>
                          <Sparkline
                            data={item.metric_trend}
                            color={item.severity === "Critical" ? "#EF4444" : "#F59E0B"}
                            width={45}
                            height={14}
                          />
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <button
                          onClick={() => {
                            if (item.action_label === "Take Action") {
                              handleExecute(item.id, item.action_type);
                            } else {
                              setSelectedAlert(item);
                            }
                          }}
                          className={`px-3 py-1 rounded-xl text-xs font-semibold cursor-pointer transition-all ${
                            item.action_label === "Take Action"
                              ? "bg-[#E85D35] hover:bg-[#D54D26] text-white"
                              : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                          }`}
                        >
                          {item.action_label}
                        </button>
                      </td>
                      <td className="p-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            item.status === "Open"
                              ? "bg-red-50 text-red-600"
                              : item.status === "Investigating"
                              ? "bg-orange-50 text-orange-600"
                              : "bg-emerald-50 text-emerald-600"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Recommended Actions & Automation Rules */}
        <div className="space-y-6">
          {/* Recommended Actions */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Recommended Actions</h3>
              <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                <Sparkles className="w-3 h-3" /> AI Powered
              </span>
            </div>

            <div className="space-y-3">
              {recommendations.map((rec) => (
                <div key={rec.id} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-start gap-2.5 flex-1 min-w-0">
                    <div className="p-2 rounded-xl bg-white shadow-xs shrink-0 mt-0.5">
                      {getActionIcon(rec.icon_name)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-bold text-slate-900 truncate">{rec.title}</div>
                      <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{rec.description}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleExecute(rec.id, rec.action_type)}
                    disabled={executeActionMutation.isPending}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold cursor-pointer shrink-0 transition-transform active:scale-95 shadow-xs ${getButtonVariantStyles(
                      rec.button_variant
                    )}`}
                  >
                    {executeActionMutation.isPending ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      rec.button_label
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Automation Rules */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Automation Rules</h3>
              <button className="text-xs text-[#E85D35] font-semibold hover:underline flex items-center gap-0.5">
                View All <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-3.5">
              {rules.map((rule) => (
                <div key={rule.id} className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-2 rounded-xl bg-slate-100 shrink-0">
                      {getAutomationIcon(rule.icon_name)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-bold text-slate-800 truncate">{rule.title}</div>
                      <div className="text-[10px] text-slate-400">{rule.description}</div>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <button
                    onClick={() =>
                      toggleRuleMutation.mutate({ ruleId: rule.id, enabled: !rule.enabled })
                    }
                    className={`w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors shrink-0 ${
                      rule.enabled ? "bg-[#10B981]" : "bg-slate-300"
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        rule.enabled ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Alert Trends (Stacked Bars) + Alert Sources (Donut) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert Trends Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm">Alert Trends</h3>
            <div className="flex items-center gap-4 text-xs font-medium">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]"></span>
                <span className="text-slate-600">Critical</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]"></span>
                <span className="text-slate-600">Warning</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
                <span className="text-slate-600">Info</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span>
                <span className="text-slate-600">Resolved</span>
              </div>
              <span className="text-slate-400">Last 7 Days →</span>
            </div>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="day" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E2E8F0", fontSize: "12px" }} />
                <Bar dataKey="Critical" stackId="a" fill="#EF4444" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Warning" stackId="a" fill="#F59E0B" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Info" stackId="a" fill="#3B82F6" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Resolved" stackId="a" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alert Sources Donut */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-900 text-sm">Alert Sources</h3>
          </div>

          <div className="flex items-center justify-center relative my-1">
            <div className="w-32 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={sourceDonut} innerRadius={42} outerRadius={60} paddingAngle={3} dataKey="value">
                    {sourceDonut.map((entry, index) => (
                      <Cell key={`cell-source-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-xl font-bold font-serif text-slate-900">{totalAlerts}</span>
              <span className="text-[10px] text-slate-400 font-medium">Total Alerts</span>
            </div>
          </div>

          <div className="space-y-1.5 text-xs pt-2 border-t border-slate-100">
            {sourceDonut.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></span>
                  <span className="text-slate-600">{item.name}</span>
                </div>
                <span className="font-bold text-slate-900">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
