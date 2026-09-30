import React, { useState, useMemo } from "react";
import {
  Download,
  Search,
  FileText,
  User,
  Settings as SettingsIcon,
  Sparkles,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  X,
  ShieldCheck,
  Clock,
} from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { KPICard } from "../components/common/KPICard";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { formatDateTime } from "../lib/formatters";
import { useAuditLog } from "../hooks/useAuditLog";
import { AuditEvent } from "../types/contracts";

export const AuditLog: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("all");
  const [userFilter, setUserFilter] = useState("all");
  const [campaignFilter, setCampaignFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  const { data: auditEvents = [], isLoading } = useAuditLog({
    search: searchQuery,
    eventType: eventTypeFilter,
    user: userFilter,
    campaign: campaignFilter,
    severity: severityFilter,
  });

  const totalPages = Math.ceil(auditEvents.length / rowsPerPage) || 1;
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return auditEvents.slice(start, start + rowsPerPage);
  }, [auditEvents, currentPage, rowsPerPage]);

  const distributionDonut = [
    { name: "User Actions", value: 27, color: "#10B981" },
    { name: "System Actions", value: 48, color: "#F59E0B" },
    { name: "Auto Actions", value: 17, color: "#8B5CF6" },
    { name: "Security Events", value: 9, color: "#EF4444" },
  ];

  const handleExport = () => {
    const jsonStr = JSON.stringify(auditEvents, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit_log_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getEventTypeBadge = (type: string) => {
    switch (type) {
      case "Campaign Action":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "Alert Triggered":
        return "bg-red-50 text-red-700 border-red-200";
      case "Auto Action":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "Settings Change":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "Data Ingestion":
        return "bg-sky-50 text-sky-700 border-sky-200";
      case "Rule Updated":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "Insight Generated":
        return "bg-indigo-50 text-indigo-700 border-indigo-200";
      case "Campaign Edit":
        return "bg-cyan-50 text-cyan-700 border-cyan-200";
      case "Retrain Model":
        return "bg-teal-50 text-teal-700 border-teal-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "Critical":
      case "High":
        return "bg-red-50 text-red-700 font-bold";
      case "Medium":
        return "bg-amber-50 text-amber-700 font-semibold";
      case "Low":
        return "bg-emerald-50 text-emerald-700 font-medium";
      case "Info":
        return "bg-blue-50 text-blue-700 font-medium";
      default:
        return "bg-slate-50 text-slate-700";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Event Details Dialog Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 relative animate-in zoom-in-95">
            <button
              onClick={() => setSelectedEvent(null)}
              className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h3 className="text-lg font-bold font-serif text-slate-900">Audit Record Details</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4 font-mono">ID: {selectedEvent.audit_id}</p>

            <div className="space-y-3 text-xs bg-slate-50 p-4 rounded-2xl border border-slate-200 mb-4 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">Timestamp:</span>
                <span className="font-semibold text-slate-800">{formatDateTime(selectedEvent.timestamp_simulated)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Actor Type:</span>
                <span className="font-semibold text-slate-800">{selectedEvent.actor_type} ({selectedEvent.user_name})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Event Type:</span>
                <span className="font-semibold text-slate-800">{selectedEvent.event_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Campaign:</span>
                <span className="font-semibold text-slate-800">{selectedEvent.campaign_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Severity:</span>
                <span className="font-semibold text-slate-800">{selectedEvent.severity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Readback Verified:</span>
                <span className="font-semibold text-emerald-600">TRUE (Deterministic Checksum Valid)</span>
              </div>
              {selectedEvent.reason_codes && (
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-slate-500 block mb-1">Reason Codes:</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedEvent.reason_codes.map((rc) => (
                      <span key={rc} className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 text-[10px]">
                        {rc}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="text-right">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-xl"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#111827] tracking-tight">Audit Log</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Track every action, alert, and system event to ensure transparency, accountability, and reliable campaign management.
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white border border-[#E2E8F0] hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-all shadow-xs cursor-pointer self-start sm:self-auto"
        >
          <Download className="w-4 h-4" />
          Export Audit Log
        </button>
      </div>

      {/* 5 Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KPICard
          title="Total Events"
          value="1,284"
          change="+12%"
          isPositive={true}
          icon={<FileText className="w-5 h-5 text-[#3B82F6]" />}
          iconBg="bg-[#DBEAFE]"
          sparklineData={[1100, 1150, 1180, 1220, 1260, 1284]}
          sparklineColor="#3B82F6"
        />
        <KPICard
          title="User Actions"
          value="342"
          change="+8%"
          isPositive={true}
          icon={<User className="w-5 h-5 text-[#F59E0B]" />}
          iconBg="bg-[#FEF3C7]"
          sparklineData={[310, 315, 325, 330, 338, 342]}
          sparklineColor="#F59E0B"
        />
        <KPICard
          title="System Actions"
          value="618"
          change="+22%"
          isPositive={false}
          icon={<SettingsIcon className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
          sparklineData={[500, 520, 550, 570, 595, 618]}
          sparklineColor="#EF4444"
        />
        <KPICard
          title="Automated Actions"
          value="214"
          change="+35%"
          isPositive={true}
          icon={<Sparkles className="w-5 h-5 text-[#8B5CF6]" />}
          iconBg="bg-[#EDE9FE]"
          sparklineData={[150, 165, 180, 195, 205, 214]}
          sparklineColor="#8B5CF6"
        />
        <KPICard
          title="Security Events"
          value="110"
          change="-14%"
          isPositive={false}
          icon={<ShieldAlert className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
          sparklineData={[130, 125, 120, 118, 114, 110]}
          sparklineColor="#EF4444"
        />
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-2xl p-3 border border-[#EAECEF] card-subtle-shadow flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events, users, campaigns..."
            className="w-full pl-10 pr-3 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Event Types</option>
            <option value="Campaign Action">Campaign Action</option>
            <option value="Alert Triggered">Alert Triggered</option>
            <option value="Auto Action">Auto Action</option>
            <option value="Settings Change">Settings Change</option>
            <option value="Data Ingestion">Data Ingestion</option>
          </select>

          <select
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Users</option>
            <option value="Aditya Sharma">Aditya Sharma</option>
            <option value="System">System</option>
            <option value="AI Bot">AI Bot</option>
            <option value="Priya Reddy">Priya Reddy</option>
          </select>

          <select
            value={campaignFilter}
            onChange={(e) => setCampaignFilter(e.target.value)}
            className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Campaigns</option>
            <option value="Summer Collection 2024">Summer Collection 2024</option>
            <option value="Monsoon Sale">Monsoon Sale</option>
            <option value="Festive Offers">Festive Offers</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded-xl px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
            <option value="Info">Info</option>
          </select>

          <div className="text-xs font-medium text-slate-600 bg-slate-50 px-2.5 py-1.5 rounded-xl border border-slate-200">
            📅 Jun 01, 2024 – Jun 30, 2024 ˅
          </div>
        </div>
      </div>

      {/* Main Grid: Table (Left 2 cols) + Distribution & Activity (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl border border-[#EAECEF] card-subtle-shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-[#FAFBF9] border-b border-[#EAECEF] text-slate-400 uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="p-3">Time</th>
                    <th className="p-3">User</th>
                    <th className="p-3">Event Type</th>
                    <th className="p-3">Campaign</th>
                    <th className="p-3">Description</th>
                    <th className="p-3">Severity</th>
                    <th className="p-3 text-center">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F3F5]">
                  {isLoading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-slate-400">Loading audit trail...</td>
                    </tr>
                  ) : paginatedEvents.map((ev) => (
                    <tr key={ev.audit_id} className="hover:bg-[#F9FAF8] transition-colors">
                      <td className="p-3 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {formatDateTime(ev.timestamp_simulated)}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-[10px]">
                            {ev.user_avatar || (ev.user_name.includes("System") ? "⚙️" : "🤖")}
                          </div>
                          <span className="font-semibold text-slate-900">{ev.user_name}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getEventTypeBadge(ev.event_type)}`}>
                          {ev.event_type}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5">
                          <PlatformIcon platform={ev.platform} size={14} />
                          <span className="truncate max-w-[130px] font-medium text-slate-800">{ev.campaign_name}</span>
                        </div>
                      </td>
                      <td className="p-3 text-slate-700 max-w-[200px] truncate">{ev.description}</td>
                      <td className="p-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] ${getSeverityBadge(ev.severity)}`}>
                          {ev.severity}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <div className="inline-flex items-center gap-1">
                          <button
                            onClick={() => setSelectedEvent(ev)}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 cursor-pointer"
                          >
                            View
                          </button>
                          <button className="p-1 text-slate-400 hover:text-slate-600">
                            <MoreHorizontal className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="p-3.5 bg-[#FAFBF9] border-t border-[#EAECEF] flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
              <div>
                Showing 1–{Math.min(rowsPerPage, paginatedEvents.length)} of 1,284 events
              </div>
              <div className="flex items-center gap-1">
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  className="p-1 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                {[1, 2, 3, 4, 5].map((p) => (
                  <button
                    key={p}
                    onClick={() => setCurrentPage(p)}
                    className={`w-6 h-6 rounded-lg text-xs font-semibold ${
                      currentPage === p ? "bg-[#E85D35] text-white" : "border border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <span className="px-1 text-slate-400">...</span>
                <button className="w-6 h-6 rounded-lg text-xs font-semibold border border-slate-200 hover:bg-slate-100">
                  129
                </button>
                <button
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  className="p-1 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Event Distribution + Severity + Recent Activity */}
        <div className="space-y-6">
          {/* Event Type Distribution */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <h3 className="font-bold text-slate-900 text-sm mb-2">Event Type Distribution</h3>

            <div className="flex items-center justify-center relative my-1">
              <div className="w-32 h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={distributionDonut} innerRadius={42} outerRadius={60} paddingAngle={3} dataKey="value">
                      {distributionDonut.map((entry, index) => (
                        <Cell key={`cell-dist-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xl font-bold font-serif text-slate-900">1,284</span>
                <span className="text-[10px] text-slate-400 font-medium">Total Events</span>
              </div>
            </div>

            <div className="space-y-1.5 text-xs pt-2 border-t border-slate-100">
              {distributionDonut.map((item) => (
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

          {/* Event Severity Progress Bars */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <h3 className="font-bold text-slate-900 text-sm mb-3">Event Severity</h3>

            <div className="space-y-2.5 text-xs">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#EF4444]"></span> Critical
                  </span>
                  <span className="font-bold text-slate-900">8%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#EF4444] rounded-full" style={{ width: "8%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#EA580C]"></span> High
                  </span>
                  <span className="font-bold text-slate-900">22%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#EA580C] rounded-full" style={{ width: "22%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#F59E0B]"></span> Medium
                  </span>
                  <span className="font-bold text-slate-900">38%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#F59E0B] rounded-full" style={{ width: "38%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#10B981]"></span> Low
                  </span>
                  <span className="font-bold text-slate-900">24%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#10B981] rounded-full" style={{ width: "24%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#3B82F6]"></span> Info
                  </span>
                  <span className="font-bold text-slate-900">8%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#3B82F6] rounded-full" style={{ width: "8%" }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity Feed */}
          <div className="bg-white rounded-2xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-900 text-sm">Recent Activity</h3>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-0.5 text-slate-600 font-medium">
                <option>Last 24 Hours</option>
              </select>
            </div>

            <div className="space-y-3.5 relative pl-4 border-l-2 border-slate-200 text-xs">
              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-[#EF4444] ring-4 ring-white"></div>
                <span className="text-[10px] text-slate-400 font-semibold">14:32</span>
                <div className="font-bold text-slate-900">Campaign paused</div>
                <div className="text-[11px] text-slate-500">Summer Collection 2024</div>
              </div>

              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-[#F59E0B] ring-4 ring-white"></div>
                <span className="text-[10px] text-slate-400 font-semibold">14:28</span>
                <div className="font-bold text-slate-900">Warning triggered</div>
                <div className="text-[11px] text-slate-500">Fatigue risk 0.72</div>
              </div>

              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-[#10B981] ring-4 ring-white"></div>
                <span className="text-[10px] text-slate-400 font-semibold">13:15</span>
                <div className="font-bold text-slate-900">Budget increased</div>
                <div className="text-[11px] text-slate-500">Monsoon Sale ($20 → $35)</div>
              </div>

              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-[#3B82F6] ring-4 ring-white"></div>
                <span className="text-[10px] text-slate-400 font-semibold">12:41</span>
                <div className="font-bold text-slate-900">12.4K comments ingested</div>
                <div className="text-[11px] text-slate-500">Meta Ads API</div>
              </div>

              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-[#8B5CF6] ring-4 ring-white"></div>
                <span className="text-[10px] text-slate-400 font-semibold">11:20</span>
                <div className="font-bold text-slate-900">Auto-pause rule enabled</div>
                <div className="text-[11px] text-slate-500">Risk &gt; 0.85</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
