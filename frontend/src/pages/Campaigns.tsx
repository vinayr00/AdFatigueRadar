import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  Eye,
  Play,
  AlertTriangle,
  Pause,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  ArrowRight,
  Activity,
  MessageSquare,
  Sparkles,
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
} from "recharts";
import { KPICard } from "../components/common/KPICard";
import { StatusBadge } from "../components/common/StatusBadge";
import { RiskBadge } from "../components/common/RiskBadge";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { Sparkline } from "../components/common/Sparkline";
import { formatNumber, formatCurrency, formatPercent } from "../lib/formatters";
import { useCampaigns, usePauseCampaign, useUnpauseCampaign } from "../hooks/useCampaigns";
import { useUIStore } from "../store/uiStore";
import { Campaign } from "../types/contracts";

export const Campaigns: React.FC = () => {
  const navigate = useNavigate();
  const { setCreateCampaignModalOpen } = useUIStore();
  const [activeTab, setActiveTab] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [rowsPerPage] = useState<number>(5);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [metric1, setMetric1] = useState<string>("impressions");
  const [metric2, setMetric2] = useState<string>("risk_score");

  const { data: campaigns = [], isLoading } = useCampaigns();
  const pauseMutation = usePauseCampaign();
  const unpauseMutation = useUnpauseCampaign();

  // Dynamic Summary Counts
  const totalCampaigns = campaigns.length;
  const activeCount = campaigns.filter((c) => c.status === "ACTIVE").length;
  const warningCount = campaigns.filter((c) => c.status === "WARNING").length;
  const pausedCount = campaigns.filter((c) => c.status === "PAUSED").length;
  const completedCount = campaigns.filter((c) => c.status === "COMPLETED").length;

  // Filtered campaigns
  const filteredCampaigns = useMemo(() => {
    return campaigns.filter((camp) => {
      if (activeTab !== "all" && camp.status.toLowerCase() !== activeTab.toLowerCase()) {
        return false;
      }
      if (statusFilter !== "all" && camp.status.toLowerCase() !== statusFilter.toLowerCase()) {
        return false;
      }
      if (platformFilter !== "all" && camp.platform.toLowerCase() !== platformFilter.toLowerCase()) {
        return false;
      }
      if (riskFilter !== "all") {
        if (riskFilter === "high" && camp.risk_score < 0.65) return false;
        if (riskFilter === "medium" && (camp.risk_score < 0.40 || camp.risk_score >= 0.65)) return false;
        if (riskFilter === "low" && camp.risk_score >= 0.40) return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return camp.name.toLowerCase().includes(q) || camp.category.toLowerCase().includes(q);
      }
      return true;
    });
  }, [campaigns, activeTab, statusFilter, platformFilter, riskFilter, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredCampaigns.length / rowsPerPage) || 1;
  const paginatedCampaigns = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return filteredCampaigns.slice(start, start + rowsPerPage);
  }, [filteredCampaigns, currentPage, rowsPerPage]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(paginatedCampaigns.map((c) => c.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  // Donut chart data for Campaign Overview
  const donutData = [
    { name: "Active", value: activeCount, color: "#10B981" },
    { name: "Warning", value: warningCount, color: "#F59E0B" },
    { name: "Paused", value: pausedCount, color: "#3B82F6" },
    { name: "Completed", value: completedCount, color: "#8B5CF6" },
  ];

  // Performance Trend series
  const trendData = [
    { day: "Jun 1", impressions: 120000, risk_score: 0.15 },
    { day: "Jun 5", impressions: 240000, risk_score: 0.22 },
    { day: "Jun 10", impressions: 380000, risk_score: 0.31 },
    { day: "Jun 15", impressions: 290000, risk_score: 0.45 },
    { day: "Jun 20", impressions: 510000, risk_score: 0.52 },
    { day: "Jun 25", impressions: 460000, risk_score: 0.72 },
    { day: "Jun 30", impressions: 680000, risk_score: 0.68 },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Campaigns</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Manage, monitor and analyze all your ad campaigns in one place.
          </p>
        </div>
        <button
          onClick={() => setCreateCampaignModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#E85D35] hover:bg-[#D54D26] text-white text-sm font-semibold transition-all shadow-sm hover:shadow-md cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          Create Campaign
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-[#E5E7EB] text-sm font-medium">
        {[
          { id: "all", label: "All Campaigns" },
          { id: "active", label: "Active" },
          { id: "warning", label: "Warning" },
          { id: "paused", label: "Paused" },
          { id: "completed", label: "Completed" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setCurrentPage(1);
            }}
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

      {/* 5 KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KPICard
          title="Total Campaigns"
          value={totalCampaigns}
          change="+20%"
          isPositive={true}
          icon={<Eye className="w-5 h-5 text-[#10B981]" />}
          iconBg="bg-[#D1FAE5]"
          sparklineData={[8, 9, 10, 10, 11, 12]}
          sparklineColor="#10B981"
        />
        <KPICard
          title="Active Campaigns"
          value={activeCount}
          change="+14%"
          isPositive={true}
          icon={<Play className="w-5 h-5 text-[#F59E0B] fill-current" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={[6, 7, 7, 8, 8, 8]}
          sparklineColor="#F59E0B"
        />
        <KPICard
          title="At Risk"
          value={warningCount}
          change="-33%"
          isPositive={false}
          icon={<AlertTriangle className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
          sparklineData={[4, 3, 3, 2, 2, 2]}
          sparklineColor="#EF4444"
        />
        <KPICard
          title="Paused"
          value={pausedCount}
          change="-50%"
          isPositive={false}
          icon={<Pause className="w-5 h-5 text-[#3B82F6] fill-current" />}
          iconBg="bg-[#DBEAFE]"
          sparklineData={[2, 2, 2, 1, 1, 1]}
          sparklineColor="#3B82F6"
        />
        <KPICard
          title="Completed"
          value={completedCount}
          change="+100%"
          isPositive={true}
          icon={<CheckCircle2 className="w-5 h-5 text-[#8B5CF6]" />}
          iconBg="bg-[#EDE9FE]"
          sparklineData={[0, 0, 1, 1, 1, 1]}
          sparklineColor="#8B5CF6"
        />
      </div>

      {/* Main Content Grid: Table on Left + 2 Panels on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Filter bar + Campaign Table */}
        <div className="lg:col-span-2 space-y-4">
          {/* Filter Bar */}
          <div className="bg-white rounded-2xl p-3 border border-[#EAECEF] card-subtle-shadow flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search campaigns..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#2D5A3C]"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={platformFilter}
                onChange={(e) => setPlatformFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 cursor-pointer focus:outline-none"
              >
                <option value="all">Platform</option>
                <option value="meta">Meta Ads</option>
                <option value="google">Google Ads</option>
                <option value="tiktok">TikTok Ads</option>
                <option value="youtube">YouTube Ads</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 cursor-pointer focus:outline-none"
              >
                <option value="all">Status</option>
                <option value="active">Active</option>
                <option value="warning">Warning</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>

              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-3 py-1.5 font-medium text-slate-700 cursor-pointer focus:outline-none"
              >
                <option value="all">Risk Level</option>
                <option value="high">High (&gt;0.65)</option>
                <option value="medium">Medium (0.40 - 0.65)</option>
                <option value="low">Low (&lt;0.40)</option>
              </select>

              {(searchQuery || platformFilter !== "all" || statusFilter !== "all" || riskFilter !== "all") && (
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setPlatformFilter("all");
                    setStatusFilter("all");
                    setRiskFilter("all");
                  }}
                  className="text-xs text-[#E85D35] font-semibold hover:underline px-2"
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>

          {/* Campaign Table Card */}
          <div className="bg-white rounded-2xl border border-[#EAECEF] card-subtle-shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-[#FAFBF9] border-b border-[#EAECEF] text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="p-3.5 w-8">
                      <input
                        type="checkbox"
                        onChange={handleSelectAll}
                        checked={
                          paginatedCampaigns.length > 0 &&
                          selectedIds.length === paginatedCampaigns.length
                        }
                        className="rounded text-emerald-700 focus:ring-0"
                      />
                    </th>
                    <th className="p-3.5">Campaign</th>
                    <th className="p-3.5">Platform</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Risk Score</th>
                    <th className="p-3.5">Impressions</th>
                    <th className="p-3.5">CTR</th>
                    <th className="p-3.5">CPA</th>
                    <th className="p-3.5">Last 7 Days</th>
                    <th className="p-3.5 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F3F5]">
                  {isLoading ? (
                    <tr>
                      <td colSpan={10} className="text-center py-8 text-slate-400">
                        Loading campaign telemetry...
                      </td>
                    </tr>
                  ) : paginatedCampaigns.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="text-center py-8 text-slate-400">
                        No campaigns match the selected filters.
                      </td>
                    </tr>
                  ) : (
                    paginatedCampaigns.map((camp) => (
                      <tr
                        key={camp.id}
                        className="hover:bg-[#F9FAF8] transition-colors group cursor-pointer"
                        onClick={() => navigate(`/live-monitor?campaign=${camp.id}`)}
                      >
                        <td className="p-3.5" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(camp.id)}
                            onChange={() => handleSelectRow(camp.id)}
                            className="rounded text-emerald-700 focus:ring-0"
                          />
                        </td>
                        <td className="p-3.5">
                          <div className="flex items-center gap-3">
                            <img
                              src={camp.thumbnail_url}
                              alt={camp.name}
                              className="w-9 h-9 rounded-xl object-cover shrink-0 border border-slate-200"
                            />
                            <div>
                              <div className="font-semibold text-slate-900 group-hover:text-[#2D5A3C] transition-colors">
                                {camp.name}
                              </div>
                              <div className="text-[10px] text-slate-400">{camp.date_range}</div>
                            </div>
                          </div>
                        </td>
                        <td className="p-3.5">
                          <PlatformIcon platform={camp.platform} size={18} />
                        </td>
                        <td className="p-3.5">
                          <StatusBadge status={camp.status} />
                        </td>
                        <td className="p-3.5">
                          <RiskBadge score={camp.risk_score} />
                        </td>
                        <td className="p-3.5 font-medium text-slate-900">
                          {formatNumber(camp.impressions, true)}
                        </td>
                        <td className="p-3.5 font-medium text-slate-900">
                          {formatPercent(camp.ctr)}
                        </td>
                        <td className="p-3.5 font-medium text-slate-900">
                          {formatCurrency(camp.cpa)}
                        </td>
                        <td className="p-3.5">
                          <Sparkline
                            data={camp.last_7_days_trend}
                            color={camp.risk_score >= 0.65 ? "#EF4444" : "#10B981"}
                            width={70}
                            height={20}
                          />
                        </td>
                        <td className="p-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                          <div className="inline-flex items-center gap-1">
                            <button
                              onClick={() => {
                                if (camp.status === "PAUSED") {
                                  unpauseMutation.mutate(camp.id);
                                } else {
                                  pauseMutation.mutate(camp.id);
                                }
                              }}
                              title={camp.status === "PAUSED" ? "Resume Campaign" : "Pause Campaign"}
                              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination footer */}
            <div className="p-3.5 bg-[#FAFBF9] border-t border-[#EAECEF] flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
              <div>
                Showing {Math.min(1, filteredCampaigns.length)}–
                {Math.min(currentPage * rowsPerPage, filteredCampaigns.length)} of{" "}
                {filteredCampaigns.length} campaigns
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                {Array.from({ length: totalPages }).map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentPage(idx + 1)}
                    className={`w-7 h-7 rounded-lg text-xs font-semibold ${
                      currentPage === idx + 1
                        ? "bg-[#E85D35] text-white"
                        : "border border-slate-200 hover:bg-slate-100 text-slate-700"
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
                <button
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Campaign Overview + Platform Distribution */}
        <div className="space-y-6">
          {/* Campaign Overview Card (Donut Chart) */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Campaign Overview</h3>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
                <option>Last 30 Days</option>
                <option>Last 7 Days</option>
              </select>
            </div>

            <div className="flex items-center justify-center relative my-2">
              <div className="w-36 h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={donutData}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {donutData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-bold font-serif text-slate-900">{totalCampaigns}</span>
                <span className="text-[10px] text-slate-400 font-medium">Total Campaigns</span>
              </div>
            </div>

            <div className="space-y-2 mt-4 pt-3 border-t border-slate-100 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span>
                  <span className="text-slate-600">Active</span>
                </div>
                <span className="font-semibold text-slate-900">{activeCount} ({Math.round((activeCount / totalCampaigns) * 100)}%)</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]"></span>
                  <span className="text-slate-600">Warning</span>
                </div>
                <span className="font-semibold text-slate-900">{warningCount} ({Math.round((warningCount / totalCampaigns) * 100)}%)</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
                  <span className="text-slate-600">Paused</span>
                </div>
                <span className="font-semibold text-slate-900">{pausedCount} ({Math.round((pausedCount / totalCampaigns) * 100)}%)</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6]"></span>
                  <span className="text-slate-600">Completed</span>
                </div>
                <span className="font-semibold text-slate-900">{completedCount} ({Math.round((completedCount / totalCampaigns) * 100)}%)</span>
              </div>
            </div>
          </div>

          {/* Platform Distribution Card */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Platform Distribution</h3>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-600">
                <option>All Campaigns</option>
              </select>
            </div>

            <div className="space-y-3.5">
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform="meta" size={16} />
                    <span className="font-medium text-slate-700">Meta Ads</span>
                  </div>
                  <span className="font-bold text-slate-900">42%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-[#10B981] rounded-full" style={{ width: "42%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform="google" size={16} />
                    <span className="font-medium text-slate-700">Google Ads</span>
                  </div>
                  <span className="font-bold text-slate-900">33%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-[#F59E0B] rounded-full" style={{ width: "33%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform="tiktok" size={16} />
                    <span className="font-medium text-slate-700">TikTok Ads</span>
                  </div>
                  <span className="font-bold text-slate-900">17%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-[#EF4444] rounded-full" style={{ width: "17%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform="youtube" size={16} />
                    <span className="font-medium text-slate-700">YouTube Ads</span>
                  </div>
                  <span className="font-bold text-slate-900">8%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-[#8B5CF6] rounded-full" style={{ width: "8%" }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Performance Trend + Recent Campaign Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Trend Chart (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-sm">Performance Trend</h3>
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
                <option value="risk_score">Risk Score</option>
                <option value="cpa">CPA</option>
              </select>
            </div>

            <div className="text-xs text-slate-500 font-medium flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
              <span>📅 Jun 01, 2024 – Jun 30, 2024 →</span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorImp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EA580C" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#EA580C" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis yAxisId="left" stroke="#94A3B8" fontSize={11} tickLine={false} tickFormatter={(v) => `${v / 1000}K`} />
                <YAxis yAxisId="right" orientation="right" stroke="#EA580C" fontSize={11} tickLine={false} domain={[0, 1.0]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E2E8F0", fontSize: "12px" }}
                />
                <Area yAxisId="left" type="monotone" dataKey="impressions" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorImp)" name="Impressions" />
                <Line yAxisId="right" type="monotone" dataKey="risk_score" stroke="#EA580C" strokeWidth={2.5} dot={{ r: 3, fill: "#EA580C" }} name="Risk Score" />
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
              <span className="text-slate-600 font-medium">Risk Score</span>
            </div>
          </div>
        </div>

        {/* Recent Campaign Activity (1 col) */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Recent Campaign Activity</h3>
              <button
                onClick={() => navigate("/audit-log")}
                className="text-xs text-[#E85D35] font-semibold hover:underline flex items-center gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 border border-amber-200">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-800">Risk score increased for Summer Collection 2024</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">From 0.58 to 0.72 • 2 hours ago</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 border border-red-200">
                  <Activity className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-800">Audience fatigue detected</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Monsoon Sale • 5 hours ago</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-200">
                  <Pause className="w-4 h-4 fill-current" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-800">Campaign paused automatically</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Retargeting – Website • 1 day ago</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0 border border-purple-200">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-800">New comments spike detected</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">New Product Launch • 1 day ago</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-800">Campaign completed</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Festive Offers • 3 days ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
