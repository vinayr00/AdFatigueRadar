import React, { useState } from "react";
import {
  Download,
  Eye,
  MousePointerClick,
  ShoppingCart,
  DollarSign,
  Target,
  Bell,
  Info,
  ArrowRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { KPICard } from "../components/common/KPICard";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { RiskBadge } from "../components/common/RiskBadge";
import { Sparkline } from "../components/common/Sparkline";
import { formatNumber, formatCurrency, formatPercent } from "../lib/formatters";
import { useAnalytics } from "../hooks/useAnalytics";
import { useCampaigns } from "../hooks/useCampaigns";
import { useNavigate } from "react-router-dom";

export const Analytics: React.FC = () => {
  const navigate = useNavigate();
  const [dateRange, setDateRange] = useState("Jun 01, 2024 – Jun 30, 2024");
  const [selectedCampaign, setSelectedCampaign] = useState("all");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [metric1, setMetric1] = useState("impressions");
  const [metric2, setMetric2] = useState("conversions");
  const [audienceTab, setAudienceTab] = useState<"demographics" | "locations" | "devices" | "interests">("demographics");

  const { data: analytics, isLoading } = useAnalytics();
  const { data: campaigns = [] } = useCampaigns();

  if (isLoading || !analytics) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-400 text-sm animate-pulse">Loading deep analytics telemetry...</div>
      </div>
    );
  }

  const sentimentDonut = [
    { name: "Positive", value: analytics.sentiment_overview.positive_pct, color: "#10B981" },
    { name: "Neutral", value: analytics.sentiment_overview.neutral_pct, color: "#3B82F6" },
    { name: "Negative", value: analytics.sentiment_overview.negative_pct, color: "#EF4444" },
    { name: "Spam", value: analytics.sentiment_overview.spam_pct, color: "#8B5CF6" },
  ];

  const genderDonut = [
    { name: "Male", value: analytics.audience_insights.gender.male, color: "#3B82F6" },
    { name: "Female", value: analytics.audience_insights.gender.female, color: "#EC4899" },
    { name: "Other", value: analytics.audience_insights.gender.other, color: "#8B5CF6" },
  ];

  const handleExport = () => {
    const jsonStr = JSON.stringify(analytics, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ad_fatigue_analytics_report_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Filter Bar */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Analytics</h1>
            <p className="text-sm text-[#6B7280] mt-1">
              Deep insights into ad performance, audience sentiment, and fatigue trends.
            </p>
          </div>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white border border-[#E2E8F0] hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-all shadow-xs cursor-pointer self-start sm:self-auto"
          >
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>

        {/* Filters Bar */}
        <div className="bg-white rounded-2xl p-3 border border-[#EAECEF] card-subtle-shadow flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl text-xs font-medium text-slate-700">
              <span>📅</span>
              <span>{dateRange}</span>
            </div>

            <select
              value={selectedCampaign}
              onChange={(e) => setSelectedCampaign(e.target.value)}
              className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none"
            >
              <option value="all">All Campaigns</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none"
            >
              <option value="all">All Platforms</option>
              <option value="meta">Meta Ads</option>
              <option value="google">Google Ads</option>
              <option value="tiktok">TikTok Ads</option>
              <option value="youtube">YouTube Ads</option>
            </select>

            <select className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none">
              <option>All Ad Formats</option>
              <option>Single Image</option>
              <option>Video Carousel</option>
              <option>Stories / Reels</option>
            </select>

            <select className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none">
              <option>All Audiences</option>
              <option>Lookalike 1%</option>
              <option>Retargeting 30d</option>
              <option>Broad 18-45</option>
            </select>
          </div>
        </div>
      </div>

      {/* 6 Top KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard
          title="Impressions"
          value={formatNumber(analytics.impressions.value, true)}
          change={analytics.impressions.change}
          isPositive={analytics.impressions.is_positive}
          icon={<Eye className="w-5 h-5 text-[#10B981]" />}
          iconBg="bg-[#D1FAE5]"
          sparklineData={analytics.impressions.sparkline}
          sparklineColor="#10B981"
        />
        <KPICard
          title="Clicks"
          value={formatNumber(analytics.clicks.value, true)}
          change={analytics.clicks.change}
          isPositive={analytics.clicks.is_positive}
          icon={<MousePointerClick className="w-5 h-5 text-[#F59E0B]" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={analytics.clicks.sparkline}
          sparklineColor="#F59E0B"
        />
        <KPICard
          title="Conversions"
          value={formatNumber(analytics.conversions.value, true)}
          change={analytics.conversions.change}
          isPositive={analytics.conversions.is_positive}
          icon={<ShoppingCart className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
          sparklineData={analytics.conversions.sparkline}
          sparklineColor="#EF4444"
        />
        <KPICard
          title="CPA"
          value={formatCurrency(analytics.cpa.value)}
          change={analytics.cpa.change}
          isPositive={analytics.cpa.is_positive}
          icon={<DollarSign className="w-5 h-5 text-[#D97706]" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={analytics.cpa.sparkline}
          sparklineColor="#D97706"
        />
        <KPICard
          title="CPM"
          value={formatCurrency(analytics.cpm.value)}
          change={analytics.cpm.change}
          isPositive={analytics.cpm.is_positive}
          icon={<Target className="w-5 h-5 text-[#8B5CF6]" />}
          iconBg="bg-[#EDE9FE]"
          sparklineData={analytics.cpm.sparkline}
          sparklineColor="#8B5CF6"
        />
        <KPICard
          title="CTR"
          value={formatPercent(analytics.ctr.value)}
          change={analytics.ctr.change}
          isPositive={analytics.ctr.is_positive}
          icon={<Bell className="w-5 h-5 text-[#3B82F6]" />}
          iconBg="bg-[#DBEAFE]"
          sparklineData={analytics.ctr.sparkline}
          sparklineColor="#3B82F6"
        />
      </div>

      {/* Row 2: Performance Trends (2 cols) + Audience Sentiment Overview (1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Trends */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-sm">Performance Trends</h3>
              <select
                value={metric1}
                onChange={(e) => setMetric1(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium text-slate-700"
              >
                <option value="impressions">Impressions</option>
                <option value="clicks">Clicks</option>
              </select>
              <span className="text-xs text-slate-400 font-medium">vs</span>
              <select
                value={metric2}
                onChange={(e) => setMetric2(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium text-slate-700"
              >
                <option value="conversions">Conversions</option>
                <option value="cpa">CPA</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
                <option>Daily</option>
                <option>Hourly</option>
                <option>Weekly</option>
              </select>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.performance_trend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorImpA" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorConvA" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EA580C" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#EA580C" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis yAxisId="left" stroke="#94A3B8" fontSize={11} tickLine={false} tickFormatter={(v) => `${v / 1000}K`} />
                <YAxis yAxisId="right" orientation="right" stroke="#EA580C" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E2E8F0", fontSize: "12px" }} />
                <Area yAxisId="left" type="monotone" dataKey="impressions" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorImpA)" name="Impressions" />
                <Line yAxisId="right" type="monotone" dataKey="conversions" stroke="#EA580C" strokeWidth={2.5} dot={{ r: 3, fill: "#EA580C" }} name="Conversions" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-center gap-6 mt-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#3B82F6]"></span>
              <span className="text-slate-600 font-medium">Impressions</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#EA580C]"></span>
              <span className="text-slate-600 font-medium">Conversions</span>
            </div>
          </div>
        </div>

        {/* Audience Sentiment Overview */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-slate-900 text-sm">Audience Sentiment Overview</h3>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
                <option>Last 30 Days</option>
              </select>
            </div>

            <div className="flex items-center justify-center relative my-1">
              <div className="w-36 h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={sentimentDonut} innerRadius={45} outerRadius={65} paddingAngle={3} dataKey="value">
                      {sentimentDonut.map((entry, index) => (
                        <Cell key={`cell-sent-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xl font-bold font-serif text-slate-900">
                  {formatNumber(analytics.sentiment_overview.total_comments, true)}
                </span>
                <span className="text-[10px] text-slate-400 font-medium">Total Comments</span>
              </div>
            </div>

            {/* Donut Legend */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
                  <span className="text-slate-600">Positive</span>
                </div>
                <span className="font-semibold text-slate-900">{analytics.sentiment_overview.positive_pct}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#3B82F6]"></span>
                  <span className="text-slate-600">Neutral</span>
                </div>
                <span className="font-semibold text-slate-900">{analytics.sentiment_overview.neutral_pct}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#EF4444]"></span>
                  <span className="text-slate-600">Negative</span>
                </div>
                <span className="font-semibold text-slate-900">{analytics.sentiment_overview.negative_pct}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#8B5CF6]"></span>
                  <span className="text-slate-600">Spam</span>
                </div>
                <span className="font-semibold text-slate-900">{analytics.sentiment_overview.spam_pct}%</span>
              </div>
            </div>

            {/* Gradient Sentiment Bar */}
            <div className="w-full h-2.5 rounded-full bg-gradient-to-r from-[#10B981] via-[#F59E0B] to-[#EF4444] mb-3"></div>

            {/* 3 Subcards */}
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100">
              <div className="bg-slate-50 p-2 rounded-xl text-center">
                <div className="text-xs font-bold text-slate-900">{analytics.sentiment_overview.sentiment_decay}</div>
                <div className="text-[10px] text-slate-500 truncate">Sentiment Decay</div>
                <div className="text-[10px] font-semibold text-[#059669] mt-0.5">↑ +18%</div>
              </div>
              <div className="bg-slate-50 p-2 rounded-xl text-center">
                <div className="text-xs font-bold text-slate-900">{analytics.sentiment_overview.fatigue_mockery}</div>
                <div className="text-[10px] text-slate-500 truncate">Fatigue / Mockery</div>
                <div className="text-[10px] font-semibold text-[#DC2626] mt-0.5">↑ +24%</div>
              </div>
              <div className="bg-slate-50 p-2 rounded-xl text-center">
                <div className="text-xs font-bold text-slate-900">{analytics.sentiment_overview.comment_acceleration}</div>
                <div className="text-[10px] text-slate-500 truncate">Comment Accel.</div>
                <div className="text-[10px] font-semibold text-[#DC2626] mt-0.5">↓ -12%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Risk Analysis (Left) + Platform Performance (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Analysis Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-sm">Risk Analysis</h3>
              <Info className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#EA580C]"></span>
                <span className="text-slate-600 font-medium">Audience Risk</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
                <span className="text-slate-600 font-medium">Economic Risk</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6 my-2">
            {/* Circular Risk Gauge */}
            <div className="w-32 h-32 rounded-full border-8 border-orange-500 border-t-amber-400 border-r-orange-600 flex flex-col items-center justify-center shrink-0 shadow-inner bg-orange-50/20">
              <span className="text-3xl font-bold font-serif text-slate-900">{analytics.risk_analysis.audience_risk}</span>
              <span className="text-[10px] font-bold text-[#D97706] bg-[#FEF3C7] px-2 py-0.5 rounded-full mt-0.5">
                ⚠️ WARNING
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-600 font-medium mb-4">
                {analytics.risk_analysis.description}
              </p>

              {/* Threshold Multi-segment Bar */}
              <div className="space-y-1.5">
                <div className="h-4 rounded-full bg-gradient-to-r from-[#A7F3D0] via-[#FDE68A] via-70% to-[#FCA5A5] relative">
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-slate-900 rounded-full shadow"
                    style={{ left: `${analytics.risk_analysis.audience_risk * 100}%` }}
                  ></div>
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold px-1">
                  <span>0.0</span>
                  <span className="text-slate-600">WATCH 0.50</span>
                  <span className="text-[#D97706] font-bold">WARNING 0.65</span>
                  <span className="text-[#C2410C]">SOFT 0.75</span>
                  <span className="text-[#DC2626]">CRITICAL 0.85</span>
                  <span>1.0</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Platform Performance Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm">Platform Performance</h3>
            <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
              <option>Impressions</option>
              <option>Clicks</option>
              <option>Conversions</option>
            </select>
          </div>

          <div className="space-y-3">
            {analytics.platform_performance.map((item) => (
              <div key={item.platform} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2.5 w-32 shrink-0">
                  <PlatformIcon platform={item.platform} size={16} />
                  <span className="text-xs font-semibold text-slate-800">{item.name}</span>
                </div>

                <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(item.impressions / 3500000) * 100}%`,
                      backgroundColor: item.color,
                    }}
                  ></div>
                </div>

                <div className="flex items-center gap-3 w-28 justify-end text-xs">
                  <span className="font-bold text-slate-900">{formatNumber(item.impressions, true)}</span>
                  <span
                    className={`font-semibold ${
                      item.is_increase === null ? "text-slate-400" : item.is_increase ? "text-[#059669]" : "text-[#DC2626]"
                    }`}
                  >
                    {item.change_pct === null ? "Change unavailable" : `${item.is_increase ? "↑" : "↓"} ${Math.abs(item.change_pct)}%`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 4: Top Performing Campaigns (Left) + Audience Insights (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performing Campaigns Table */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-900 text-sm">Top Performing Campaigns</h3>
              <button
                onClick={() => navigate("/campaigns")}
                className="text-xs text-[#E85D35] font-semibold hover:underline flex items-center gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="border-b border-slate-100 text-slate-400 font-semibold text-[10px] uppercase">
                  <tr>
                    <th className="py-2">#</th>
                    <th className="py-2">Campaign</th>
                    <th className="py-2">Platform</th>
                    <th className="py-2">Impressions</th>
                    <th className="py-2">CTR</th>
                    <th className="py-2">CPA</th>
                    <th className="py-2">Risk Score</th>
                    <th className="py-2">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {campaigns.slice(0, 5).map((camp, idx) => (
                    <tr
                      key={camp.id}
                      onClick={() => navigate(`/live-monitor?campaign=${camp.id}`)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 font-bold text-slate-400">{idx + 1}</td>
                      <td className="py-2.5">
                        <div className="flex items-center gap-2">
                          <img src={camp.thumbnail_url} alt="" className="w-6 h-6 rounded-md object-cover" />
                          <span className="font-semibold text-slate-900">{camp.name}</span>
                        </div>
                      </td>
                      <td className="py-2.5">
                        <PlatformIcon platform={camp.platform} size={15} />
                      </td>
                      <td className="py-2.5 font-medium">{formatNumber(camp.impressions, true)}</td>
                      <td className="py-2.5 font-medium">{formatPercent(camp.ctr)}</td>
                      <td className="py-2.5 font-medium">{formatCurrency(camp.cpa)}</td>
                      <td className="py-2.5">
                        <RiskBadge score={camp.risk_score} />
                      </td>
                      <td className="py-2.5">
                        <Sparkline
                          data={camp.last_7_days_trend}
                          color={camp.risk_score >= 0.65 ? "#EF4444" : "#10B981"}
                          width={50}
                          height={16}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Audience Insights Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-slate-900 text-sm">Audience Insights</h3>
            <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
              <option>All Campaigns</option>
            </select>
          </div>

          {/* Sub-tabs */}
          <div className="flex items-center gap-4 border-b border-slate-100 text-xs font-semibold pb-2 mb-4">
            {(["demographics", "locations", "devices", "interests"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setAudienceTab(tab)}
                className={`capitalize pb-1 relative cursor-pointer ${
                  audienceTab === tab ? "text-[#E85D35]" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {tab}
                {audienceTab === tab && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#E85D35] rounded-full"></span>
                )}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Age Group Bar Chart */}
            <div>
              <span className="text-xs font-bold text-slate-800 block mb-2">Age Group</span>
              <div className="h-32 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.audience_insights.age_groups} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                    <XAxis dataKey="group" stroke="#94A3B8" fontSize={10} tickLine={false} />
                    <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} tickFormatter={(v) => `${v}%`} />
                    <Tooltip formatter={(val) => [`${val}%`, "Share"]} />
                    <Bar dataKey="percentage" fill="#818CF8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gender Donut Chart */}
            <div>
              <span className="text-xs font-bold text-slate-800 block mb-2">Gender</span>
              <div className="flex items-center justify-center relative h-32">
                <div className="w-28 h-28">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={genderDonut} innerRadius={35} outerRadius={50} paddingAngle={4} dataKey="value">
                        {genderDonut.map((entry, index) => (
                          <Cell key={`cell-gender-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="ml-3 space-y-1 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#3B82F6]"></span>
                    <span className="text-slate-600">62% Male</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#EC4899]"></span>
                    <span className="text-slate-600">36% Female</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#8B5CF6]"></span>
                    <span className="text-slate-600">2% Other</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
