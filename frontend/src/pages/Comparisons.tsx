import React, { useEffect, useState } from "react";
import {
  Download,
  Plus,
  Eye,
  MousePointerClick,
  ShoppingCart,
  DollarSign,
  Target,
  Bell,
  Trophy,
  ArrowUp,
  ArrowDown,
  Info,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { Sparkline } from "../components/common/Sparkline";
import { formatNumber, formatCurrency, formatPercent } from "../lib/formatters";
import { useComparisons } from "../hooks/useComparisons";
import { useCampaigns } from "../hooks/useCampaigns";

export const Comparisons: React.FC = () => {
  const [activeTab, setActiveTab] = useState("campaign");
  const [campaignAId, setCampaignAId] = useState("");
  const [campaignBId, setCampaignBId] = useState("");

  const { data: campaigns = [] } = useCampaigns();
  const { data: comparison, isLoading } = useComparisons(campaignAId, campaignBId);

  useEffect(() => {
    if (campaigns.length && !campaignAId) setCampaignAId(campaigns[0].id);
    if (campaigns.length > 1 && !campaignBId) setCampaignBId(campaigns[1].id);
  }, [campaigns, campaignAId, campaignBId]);

  if (!isLoading && campaigns.length < 2) {
    return <section className="m-6 rounded-2xl border border-slate-200 bg-white p-8 text-slate-700">Create or load two campaigns with backend data to compare them.</section>;
  }

  if (isLoading || !comparison) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-400 text-sm animate-pulse">Loading comparison matrices...</div>
      </div>
    );
  }

  const { campaign_a: a, campaign_b: b } = comparison;

  const handleExport = () => {
    const jsonStr = JSON.stringify(comparison, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const aEl = document.createElement("a");
    aEl.href = url;
    aEl.download = `comparison_${a.name}_vs_${b.name}.json`;
    aEl.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Comparisons</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Compare campaigns, platforms, audiences, or time periods to uncover insights and make better decisions.
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white border border-[#E2E8F0] hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-all shadow-xs cursor-pointer self-start sm:self-auto"
        >
          <Download className="w-4 h-4" />
          Export Comparison
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-[#E5E7EB] text-sm font-medium">
        {[
          { id: "campaign", label: "Campaign Comparison" },
          { id: "platform", label: "Platform Comparison" },
          { id: "audience", label: "Audience Comparison" },
          { id: "time", label: "Time Period Comparison" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
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

      {/* Campaign Selection Row */}
      <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Campaign A Dropdown */}
          <div className="flex items-center gap-3 p-2 bg-[#F8F9FA] rounded-2xl border border-slate-200 min-w-[240px]">
            <img src={a.thumbnail} alt="" className="w-9 h-9 rounded-xl object-cover" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Campaign A</span>
              <select
                value={campaignAId}
                onChange={(e) => setCampaignAId(e.target.value)}
                className="text-xs font-bold text-slate-800 bg-transparent focus:outline-none w-full cursor-pointer"
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <span className="text-xs font-black text-slate-400 bg-slate-100 px-2 py-1 rounded-full">VS</span>

          {/* Campaign B Dropdown */}
          <div className="flex items-center gap-3 p-2 bg-[#F8F9FA] rounded-2xl border border-slate-200 min-w-[240px]">
            <img src={b.thumbnail} alt="" className="w-9 h-9 rounded-xl object-cover" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Campaign B</span>
              <select
                value={campaignBId}
                onChange={(e) => setCampaignBId(e.target.value)}
                className="text-xs font-bold text-slate-800 bg-transparent focus:outline-none w-full cursor-pointer"
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Add Campaign Button */}
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-dashed border-slate-300 text-xs font-semibold text-slate-500 hover:bg-slate-50">
            <Plus className="w-3.5 h-3.5" />
            Add Campaign
          </button>
        </div>

        <div className="text-xs font-medium text-slate-600 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
          📅 Current available telemetry
        </div>
      </div>

      {/* 6 Comparison Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Impressions */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#D1FAE5] text-[#10B981] flex items-center justify-center">
              <Eye className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">Impressions</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{formatNumber(a.impressions, true)}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{formatNumber(b.impressions, true)}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[10, 14, 18, 22, 28, 35]} color="#10B981" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↑ 41%</span>
          </div>
        </div>

        {/* Clicks */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#FEF3C7] text-[#F59E0B] flex items-center justify-center">
              <MousePointerClick className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">Clicks</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{formatNumber(a.clicks, true)}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{formatNumber(b.clicks, true)}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[8, 11, 14, 16, 17, 18]} color="#F59E0B" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↑ 39%</span>
          </div>
        </div>

        {/* Conversions */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
              <ShoppingCart className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">Conversions</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{a.conversions}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{b.conversions}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[120, 160, 210, 260, 312]} color="#EF4444" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↑ 49%</span>
          </div>
        </div>

        {/* CPA */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#FEF3C7] text-[#D97706] flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">CPA</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{formatCurrency(a.cpa)}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{formatCurrency(b.cpa)}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[24, 22, 20, 19, 18.4]} color="#059669" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↓ 20%</span>
          </div>
        </div>

        {/* CPM */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#EDE9FE] text-[#8B5CF6] flex items-center justify-center">
              <Target className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">CPM</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{formatCurrency(a.cpm)}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{formatCurrency(b.cpm)}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[14, 12, 11, 10, 9.1]} color="#8B5CF6" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↓ 27%</span>
          </div>
        </div>

        {/* CTR */}
        <div className="bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#DBEAFE] text-[#3B82F6] flex items-center justify-center">
              <Bell className="w-4 h-4" />
            </div>
            <span className="text-xs text-slate-500 font-medium">CTR</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{formatPercent(a.ctr)}</span>
            <span className="text-xs text-slate-400">vs</span>
            <span className="text-sm font-semibold text-slate-600">{formatPercent(b.ctr)}</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
            <Sparkline data={[1.1, 1.2, 1.3, 1.35, 1.4]} color="#3B82F6" width={55} height={16} />
            <span className="text-xs font-bold text-[#059669]">↑ 8%</span>
          </div>
        </div>
      </div>

      {/* Row 2: Audience Fatigue Risk Comparison (Left 2 cols) + Key Insights & Winner (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Comparison Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm">Audience Fatigue Risk Comparison</h3>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#EA580C]"></span>
                <span className="text-slate-700 font-medium">{a.name}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
                <span className="text-slate-700 font-medium">{b.name}</span>
              </div>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
                <option>Last 30 Days</option>
              </select>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={comparison.risk_timeline} margin={{ top: 10, right: 30, left: -20, bottom: 0 }}>
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} domain={[0, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E2E8F0", fontSize: "12px" }} />
                <Line type="monotone" dataKey="risk_a" stroke="#EA580C" strokeWidth={2.5} dot={{ r: 3, fill: "#EA580C" }} name={a.name} />
                <Line type="monotone" dataKey="risk_b" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3, fill: "#3B82F6" }} name={b.name} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Key Comparison Insights & Winner Card */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-900 text-sm">Key Comparison Insights</h3>
              <Info className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="space-y-2.5">
              {comparison.insights.map((item, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs">
                  <span className="mt-0.5 shrink-0">
                    {item.type === "positive" && <ArrowUp className="w-3.5 h-3.5 text-[#059669]" />}
                    {item.type === "negative" && <ArrowDown className="w-3.5 h-3.5 text-[#DC2626]" />}
                    {item.type === "warning" && <ArrowUp className="w-3.5 h-3.5 text-[#D97706]" />}
                  </span>
                  <span className="text-slate-700 font-medium leading-tight">{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Overall Winner Card */}
          {comparison.winner_summary && (
            <div className="bg-gradient-to-br from-[#FFFBEB] via-[#FEF3C7] to-[#FDE68A] rounded-2xl p-4 border border-[#FDE68A] flex items-start gap-3.5 shadow-xs">
              <div className="w-10 h-10 rounded-2xl bg-[#D97706] text-white flex items-center justify-center shrink-0 shadow-sm">
                <Trophy className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-[#92400E] uppercase tracking-wider block">Comparison Synthesis</span>
                <h4 className="text-sm font-bold text-[#78350F]">{comparison.winner_summary.winner_name}</h4>
                <p className="text-xs text-[#92400E] mt-0.5">{comparison.winner_summary.summary}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Row 3: Metric Comparison Cards (Left 2 cols) + Platform Breakdown (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 5 Metric Comparison Cards */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm">Metric Comparison</h3>
            <Info className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {/* Sentiment Decay */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 font-medium">Sentiment Decay</span>
              <div className="my-2">
                <span className="text-lg font-bold text-slate-900">{a.sentiment_decay}</span>
                <span className="text-xs text-slate-400"> vs </span>
                <span className="text-xs font-semibold text-slate-600">{b.sentiment_decay}</span>
              </div>
              <div className="flex items-center justify-between">
                <Sparkline data={[0.4, 0.45, 0.52, 0.61]} color="#EF4444" width={40} height={14} />
                <span className="text-[11px] font-bold text-[#DC2626]">↑ 45%</span>
              </div>
            </div>

            {/* Negative Ratio */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 font-medium">Negative Ratio</span>
              <div className="my-2">
                <span className="text-lg font-bold text-slate-900">{a.negative_ratio}%</span>
                <span className="text-xs text-slate-400"> vs </span>
                <span className="text-xs font-semibold text-slate-600">{b.negative_ratio}%</span>
              </div>
              <div className="flex items-center justify-between">
                <Sparkline data={[14, 17, 20, 24]} color="#EF4444" width={40} height={14} />
                <span className="text-[11px] font-bold text-[#DC2626]">↑ 50%</span>
              </div>
            </div>

            {/* Comment Acceleration */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 font-medium">Comment Accel.</span>
              <div className="my-2">
                <span className="text-lg font-bold text-slate-900">{a.comment_acceleration}</span>
                <span className="text-xs text-slate-400"> vs </span>
                <span className="text-xs font-semibold text-slate-600">{b.comment_acceleration}</span>
              </div>
              <div className="flex items-center justify-between">
                <Sparkline data={[0.2, 0.28, 0.35, 0.42]} color="#EF4444" width={40} height={14} />
                <span className="text-[11px] font-bold text-[#DC2626]">↑ 50%</span>
              </div>
            </div>

            {/* CTR / Frequency */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 font-medium">CTR / Frequency</span>
              <div className="my-2">
                <span className="text-lg font-bold text-slate-900">{a.ctr_frequency}</span>
                <span className="text-xs text-slate-400"> vs </span>
                <span className="text-xs font-semibold text-slate-600">{b.ctr_frequency}</span>
              </div>
              <div className="flex items-center justify-between">
                <Sparkline data={[0.42, 0.48, 0.52, 0.58]} color="#F59E0B" width={40} height={14} />
                <span className="text-[11px] font-bold text-[#D97706]">↑ 26%</span>
              </div>
            </div>

            {/* Critical Complaints */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 font-medium">Critical Complaints</span>
              <div className="my-2">
                <span className="text-lg font-bold text-slate-900">{a.critical_complaints}</span>
                <span className="text-xs text-slate-400"> vs </span>
                <span className="text-xs font-semibold text-slate-600">{b.critical_complaints}</span>
              </div>
              <div className="flex items-center justify-between">
                <Sparkline data={[0.08, 0.12, 0.17, 0.21]} color="#EF4444" width={40} height={14} />
                <span className="text-[11px] font-bold text-[#DC2626]">↑ 91%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Platform Breakdown */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-slate-900 text-sm">Platform Breakdown</h3>
            <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
              <option>Both Campaigns</option>
            </select>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-100 text-slate-400 text-[10px] uppercase font-bold">
              <tr>
                <th className="py-2">Platform</th>
                <th className="py-2">Campaign A</th>
                <th className="py-2">Campaign B</th>
                <th className="py-2 text-right">Diff</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {comparison.platform_breakdown.map((row) => (
                <tr key={row.platform}>
                  <td className="py-2 font-semibold text-slate-800">{row.platform}</td>
                  <td className="py-2">{row.impressions_a > 0 ? formatNumber(row.impressions_a, true) : "—"}</td>
                  <td className="py-2">{row.impressions_b ? formatNumber(row.impressions_b, true) : "—"}</td>
                  <td className="py-2 text-right font-bold text-[#059669]">
                    {row.diff_pct ? `↑ ${row.diff_pct}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row 4: Comment Sentiment Comparison + Top Categories + Campaign Performance Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Comment Sentiment Comparison */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Comment Sentiment Comparison</h3>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs mb-4">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span>
                <span className="text-slate-600">Positive</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
                <span className="text-slate-600">Neutral</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]"></span>
                <span className="text-slate-600">Negative</span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-slate-800 block mb-1">{a.name}</span>
                <div className="h-6 w-full rounded-xl overflow-hidden flex text-[10px] font-bold text-white leading-6 text-center">
                  <div className="bg-[#10B981]" style={{ width: `${a.sentiment.positive}%` }}>{a.sentiment.positive}%</div>
                  <div className="bg-[#3B82F6]" style={{ width: `${a.sentiment.neutral}%` }}>{a.sentiment.neutral}%</div>
                  <div className="bg-[#EF4444]" style={{ width: `${a.sentiment.negative}%` }}>{a.sentiment.negative}%</div>
                </div>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-800 block mb-1">{b.name}</span>
                <div className="h-6 w-full rounded-xl overflow-hidden flex text-[10px] font-bold text-white leading-6 text-center">
                  <div className="bg-[#10B981]" style={{ width: `${b.sentiment.positive}%` }}>{b.sentiment.positive}%</div>
                  <div className="bg-[#3B82F6]" style={{ width: `${b.sentiment.neutral}%` }}>{b.sentiment.neutral}%</div>
                  <div className="bg-[#EF4444]" style={{ width: `${b.sentiment.negative}%` }}>{b.sentiment.negative}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Comment Categories (Comparison) */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-slate-900 text-sm">Top Comment Categories</h3>
            <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
              <option>Negative Comments</option>
            </select>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold uppercase pb-1 border-b border-slate-100">
              <span>Category</span>
              <div className="flex items-center gap-6">
                <span>A</span>
                <span>B</span>
              </div>
            </div>

            {comparison.top_comment_categories.map((cat) => (
              <div key={cat.category} className="flex items-center justify-between">
                <span className="font-medium text-slate-800">{cat.category}</span>
                <div className="flex items-center gap-3">
                  <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="bg-[#EA580C] h-full" style={{ width: `${cat.pct_a}%` }}></div>
                  </div>
                  <span className="font-bold text-slate-900 w-7 text-right">{cat.pct_a}%</span>
                  <span className="text-slate-500 w-7 text-right">{cat.pct_b}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Campaign Performance Summary Table */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <h3 className="font-bold text-slate-900 text-sm mb-3">Performance Summary</h3>

          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-100 text-slate-400 text-[10px] uppercase font-bold">
              <tr>
                <th className="py-2">Metric</th>
                <th className="py-2">Camp A</th>
                <th className="py-2">Camp B</th>
                <th className="py-2 text-right">Difference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="py-2 font-medium text-slate-600">Impressions</td>
                <td className="py-2 font-semibold text-slate-800">1.2M</td>
                <td className="py-2 text-slate-600">850K</td>
                <td className="py-2 text-right font-bold text-[#059669]">↑ 41%</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-600">Clicks</td>
                <td className="py-2 font-semibold text-slate-800">16.8K</td>
                <td className="py-2 text-slate-600">12.1K</td>
                <td className="py-2 text-right font-bold text-[#059669]">↑ 39%</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-600">CTR</td>
                <td className="py-2 font-semibold text-slate-800">1.4%</td>
                <td className="py-2 text-slate-600">1.3%</td>
                <td className="py-2 text-right font-bold text-[#059669]">↑ 8%</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-600">Conversions</td>
                <td className="py-2 font-semibold text-slate-800">312</td>
                <td className="py-2 text-slate-600">210</td>
                <td className="py-2 text-right font-bold text-[#059669]">↑ 49%</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-600">CPA</td>
                <td className="py-2 font-semibold text-slate-800">$18₹1,840</td>
                <td className="py-2 text-slate-600">$23₹2,310</td>
                <td className="py-2 text-right font-bold text-[#059669]">↓ 20%</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-600">CPM</td>
                <td className="py-2 font-semibold text-slate-800">$9₹2,310</td>
                <td className="py-2 text-slate-600">$12₹1,680</td>
                <td className="py-2 text-right font-bold text-[#059669]">↓ 27%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
