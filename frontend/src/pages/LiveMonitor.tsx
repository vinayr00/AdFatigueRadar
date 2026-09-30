import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Play,
  Pause,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Layers,
  Sparkles,
  TrendingDown,
  Info,
  Clock,
  ArrowRight,
  Flame,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { KPICard } from "../components/common/KPICard";
import { StatusBadge } from "../components/common/StatusBadge";
import { PlatformIcon } from "../components/common/PlatformIcon";
import { RiskBadge } from "../components/common/RiskBadge";
import { formatNumber, formatCurrency, formatPercent, formatDateTime } from "../lib/formatters";
import { useReplay, useStartReplay, useResetReplay } from "../hooks/useReplay";
import { useCampaign } from "../hooks/useCampaigns";
import { useReplayStore } from "../store/replayStore";
import { CommentCategory, CampaignState } from "../types/contracts";

export const LiveMonitor: React.FC = () => {
  const [searchParams] = useSearchParams();
  const campaignIdParam = searchParams.get("campaign") || "cmp_summer_2024";

  const {
    isPlaying,
    setIsPlaying,
    speed,
    setSpeed,
    currentHour,
    setCurrentHour,
    scenarioName,
    setScenarioName,
    scenarioSeed,
    setScenarioSeed,
  } = useReplayStore();

  const { data: campaign } = useCampaign(campaignIdParam);
  const { data: replay, refetch } = useReplay(campaignIdParam, speed);
  const startReplayMutation = useStartReplay();
  const resetReplayMutation = useResetReplay();

  // Simulated replay progression timer
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentHour(Math.min(72, currentHour + 0.5 * speed));
        if (currentHour >= 72) {
          setIsPlaying(false);
        }
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, speed, currentHour, setCurrentHour, setIsPlaying]);

  // Derive current telemetry step at currentHour
  const timelinePoints = replay?.points || [];
  const currentPoint = timelinePoints.reduce((prev, curr) => {
    return Math.abs(curr.hour - currentHour) < Math.abs(prev.hour - currentHour) ? curr : prev;
  }, timelinePoints[0] || {
    hour: 0,
    timestamp_simulated: "2024-06-12T00:00:00Z",
    potential_impressions: 16000,
    observed_impressions: 16000,
    potential_spend: 80,
    observed_spend: 80,
    audience_risk: 0.15,
    economic_risk: 0.12,
    cpa: 14.20,
    cpm: 9.10,
    state: "ACTIVE" as CampaignState,
  });

  const currentState = currentPoint.state || "ACTIVE";

  const handleTogglePlay = () => {
    if (!isPlaying) {
      startReplayMutation.mutate({ campaignId: campaignIdParam, speed });
      setIsPlaying(true);
    } else {
      setIsPlaying(false);
    }
  };

  const handleReset = () => {
    resetReplayMutation.mutate(campaignIdParam);
    setCurrentHour(0);
    setIsPlaying(false);
  };

  const getCategoryColor = (cat: CommentCategory) => {
    switch (cat) {
      case "fatigue":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "mockery":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "product_complaint":
      case "service_complaint":
        return "bg-red-100 text-red-800 border-red-200";
      case "spam":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "positive":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Status Bar */}
      <div className="bg-white rounded-3xl p-6 border border-[#EAECEF] card-subtle-shadow">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <img
              src={campaign?.thumbnail_url || "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=120&q=80"}
              alt=""
              className="w-16 h-16 rounded-2xl object-cover border border-slate-200 shadow-sm"
            />
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold font-serif text-slate-900">
                  {campaign?.name || "Summer Collection 2024"}
                </h1>
                <PlatformIcon platform={campaign?.platform || "meta"} size={20} />
                <StatusBadge status={currentState} />
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#E4EFE3] text-[#1E3A2B] border border-[#D0E2CF]">
                  <ShieldCheck className="w-3.5 h-3.5" /> Sandbox Safe
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 font-medium">
                <span>Category: <strong className="text-slate-700">{campaign?.category || "Fashion & Apparel"}</strong></span>
                <span>•</span>
                <span>Audience: <strong className="text-slate-700">{campaign?.target_audience || "Broad 18-45"}</strong></span>
                <span>•</span>
                <span className="font-mono">ID: {campaign?.id || campaignIdParam}</span>
              </div>
            </div>
          </div>

          {/* Quick Stats Banner */}
          <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-2xl border border-slate-200 self-start lg:self-auto">
            <div className="text-center px-2">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Simulated Time</span>
              <span className="text-xs font-mono font-bold text-slate-800">
                Hour {currentHour.toFixed(1)} / 72
              </span>
            </div>
            <div className="h-7 w-px bg-slate-200"></div>
            <div className="text-center px-2">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Audience Risk</span>
              <span className={`text-xs font-bold ${currentPoint.audience_risk >= 0.65 ? "text-[#DC2626]" : "text-[#059669]"}`}>
                {currentPoint.audience_risk.toFixed(2)}
              </span>
            </div>
            <div className="h-7 w-px bg-slate-200"></div>
            <div className="text-center px-2">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">State Machine</span>
              <span className="text-xs font-bold text-slate-800">{currentState}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Deterministic Replay Controls Bar */}
      <div className="bg-[#1E3A2B] text-white rounded-3xl p-4 sm:p-5 shadow-lg flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleTogglePlay}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#34D399] hover:bg-[#10B981] text-[#1E3A2B] text-xs font-bold transition-all shadow cursor-pointer active:scale-95"
          >
            {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
            {isPlaying ? "Pause Stream" : "Start 72h Replay"}
          </button>

          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-2xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>

          <div className="flex items-center gap-1 bg-black/20 p-1 rounded-2xl border border-white/10">
            <span className="text-[10px] text-emerald-200 px-2 font-bold uppercase">Speed:</span>
            {[1, 5, 10, 60].map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-1 rounded-xl text-xs font-bold transition-colors ${
                  speed === s
                    ? "bg-[#34D399] text-[#1E3A2B]"
                    : "text-emerald-100 hover:bg-white/10"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Scrubber */}
        <div className="flex items-center gap-4 flex-1 max-w-md min-w-[240px]">
          <span className="text-[11px] font-mono text-emerald-300 whitespace-nowrap">0h</span>
          <input
            type="range"
            min="0"
            max="72"
            step="0.5"
            value={currentHour}
            onChange={(e) => setCurrentHour(parseFloat(e.target.value))}
            className="w-full h-2 bg-emerald-950 rounded-lg appearance-none cursor-pointer accent-[#34D399]"
          />
          <span className="text-[11px] font-mono text-emerald-300 whitespace-nowrap">72h</span>
        </div>

        <div className="flex items-center gap-3 text-xs text-emerald-100">
          <span className="px-3 py-1 rounded-full bg-white/10 font-mono text-[11px]">
            Seed: {scenarioSeed}
          </span>
          <select
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            className="bg-black/30 border border-white/20 rounded-xl px-3 py-1 text-xs text-white focus:outline-none cursor-pointer"
          >
            <option value="Standard Fatigue Run (Seed #42)">Standard Fatigue (Seed #42)</option>
            <option value="CPM Spike Negative Control">CPM Spike Negative Control</option>
            <option value="Banter Storm Negative Control">Banter Storm Negative Control</option>
            <option value="Rapid Sentiment Crash">Rapid Sentiment Crash</option>
          </select>
        </div>
      </div>

      {/* 6 Dynamic KPI Metrics at Current Replay Point */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard
          title="Observed Impressions"
          value={formatNumber(currentPoint.observed_impressions, true)}
          subValue={`Pot: ${formatNumber(currentPoint.potential_impressions, true)}`}
          isPositive={currentPoint.observed_impressions > 0}
          icon={<Activity className="w-5 h-5 text-[#10B981]" />}
          iconBg="bg-[#D1FAE5]"
          sparklineData={[14000, 16000, 15000, currentPoint.observed_impressions]}
          sparklineColor="#10B981"
        />
        <KPICard
          title="Observed Spend"
          value={formatCurrency(currentPoint.observed_spend)}
          subValue={`Pot: ${formatCurrency(currentPoint.potential_spend)}`}
          isPositive={true}
          icon={<TrendingDown className="w-5 h-5 text-[#3B82F6]" />}
          iconBg="bg-[#DBEAFE]"
        />
        <KPICard
          title="Current CPA"
          value={currentPoint.cpa !== null ? formatCurrency(currentPoint.cpa) : "—"}
          subValue={currentPoint.cpa === null ? "Zero Volume" : undefined}
          isPositive={currentPoint.cpa ? currentPoint.cpa < 20 : true}
          icon={<Sparkles className="w-5 h-5 text-[#F59E0B]" />}
          iconBg="bg-[#FEF3C7]"
        />
        <KPICard
          title="Observed CPM"
          value={formatCurrency(currentPoint.cpm)}
          isPositive={true}
          icon={<Layers className="w-5 h-5 text-[#8B5CF6]" />}
          iconBg="bg-[#EDE9FE]"
        />
        <KPICard
          title="Audience Risk"
          value={currentPoint.audience_risk.toFixed(2)}
          change={currentPoint.audience_risk >= 0.65 ? "WARNING" : "HEALTHY"}
          isPositive={currentPoint.audience_risk < 0.65}
          icon={<Flame className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
        />
        <KPICard
          title="Economic Risk"
          value={currentPoint.economic_risk !== null ? currentPoint.economic_risk.toFixed(2) : "N/A"}
          subValue={currentPoint.economic_risk === null ? "< 20 conv/hr" : undefined}
          isPositive={currentPoint.economic_risk ? currentPoint.economic_risk < 0.60 : true}
          icon={<ShieldCheck className="w-5 h-5 text-[#10B981]" />}
          iconBg="bg-[#D1FAE5]"
        />
      </div>

      {/* Row 2: Risk Gauges + State Machine Flow (Left 2 cols) + Evidence Breakdown (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Risk Gauges & State Machine */}
        <div className="lg:col-span-2 space-y-6">
          {/* Dual Gauges & Current State */}
          <div className="bg-white rounded-3xl p-6 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Authoritative Risk Gauges & State Engine</h3>
                <p className="text-xs text-slate-500">Backend risk decisions with hysteresis and automatic guard protection.</p>
              </div>
              <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                Threshold: 0.65 (Warn) | 0.85 (Critical)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center my-2">
              {/* Audience Risk Gauge */}
              <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <span className="text-xs font-bold text-slate-700 mb-2">Audience Risk</span>
                <div className={`w-28 h-28 rounded-full border-8 flex flex-col items-center justify-center ${
                  currentPoint.audience_risk >= 0.65
                    ? "border-red-500 bg-red-50/50"
                    : currentPoint.audience_risk >= 0.40
                    ? "border-amber-400 bg-amber-50/50"
                    : "border-emerald-500 bg-emerald-50/50"
                }`}>
                  <span className="text-2xl font-bold font-serif text-slate-900">
                    {currentPoint.audience_risk.toFixed(2)}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500">
                    {currentPoint.audience_risk >= 0.65 ? "ELEVATED" : "NORMAL"}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 mt-2">Wilson lower-bound & decay</span>
              </div>

              {/* Economic Risk Gauge */}
              <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <span className="text-xs font-bold text-slate-700 mb-2">Economic Risk</span>
                <div className="w-28 h-28 rounded-full border-8 border-slate-300 bg-slate-100 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold font-serif text-slate-900">
                    {currentPoint.economic_risk !== null ? currentPoint.economic_risk.toFixed(2) : "N/A"}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500">
                    {currentPoint.economic_risk !== null ? "CONFIRMED" : "GATE N/A"}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 mt-2">CPA & conversion decay</span>
              </div>

              {/* State Machine Status */}
              <div className="flex flex-col justify-between h-full p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div>
                  <span className="text-xs font-bold text-slate-700 block mb-1">State Machine</span>
                  <div className="my-1">
                    <StatusBadge status={currentState} size="md" />
                  </div>
                  <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                    {replay?.state_reason || "All telemetry parameters within safety bounds."}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-200 text-[10px] text-slate-400 flex items-center justify-between">
                  <span>Hysteresis: Active</span>
                  <span>Readback: Verified ✓</span>
                </div>
              </div>
            </div>

            {/* State Machine Steps Visualizer */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <span className="text-xs font-bold text-slate-700 block mb-3">Guard State Progression</span>
              <div className="grid grid-cols-5 gap-2">
                {[
                  { key: "ACTIVE", label: "ACTIVE", color: "bg-emerald-500" },
                  { key: "WATCH", label: "WATCH (0.50)", color: "bg-amber-400" },
                  { key: "WARNING", label: "WARNING (0.65)", color: "bg-orange-500" },
                  { key: "SOFT_REDUCED", label: "SOFT REDUCED (0.8x)", color: "bg-orange-600" },
                  { key: "PAUSED", label: "PAUSED (Sandbox)", color: "bg-red-600" },
                ].map((st, idx) => (
                  <div
                    key={st.key}
                    className={`p-2 rounded-xl text-center border transition-all ${
                      currentState === st.key
                        ? "bg-slate-900 text-white font-bold border-slate-900 shadow-md scale-105"
                        : "bg-slate-50 text-slate-600 border-slate-200 opacity-60"
                    }`}
                  >
                    <div className="text-[10px] truncate">{st.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 72-Hour Main Replay Timeline Chart */}
          <div className="bg-white rounded-3xl p-6 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">72-Hour Telemetry & Risk Timeline</h3>
                <p className="text-xs text-slate-500">
                  Potential curve vs Action-responsive Observed response (Soft budget multiplier 0.80x & Zero-volume Heartbeat).
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
                  <span className="text-slate-700 font-medium">Observed Volume</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#94A3B8]"></span>
                  <span className="text-slate-500 font-medium">Potential Volume</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]"></span>
                  <span className="text-slate-700 font-medium">Audience Risk</span>
                </div>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={timelinePoints} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorObs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="hour" stroke="#94A3B8" fontSize={11} tickLine={false} tickFormatter={(h) => `${h}h`} />
                  <YAxis yAxisId="left" stroke="#94A3B8" fontSize={11} tickLine={false} tickFormatter={(v) => `${v / 1000}K`} />
                  <YAxis yAxisId="right" orientation="right" stroke="#EF4444" fontSize={11} tickLine={false} domain={[0, 1.0]} />
                  <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E2E8F0", fontSize: "12px" }} />
                  <Line yAxisId="left" type="monotone" dataKey="potential_impressions" stroke="#CBD5E1" strokeDasharray="4 4" strokeWidth={2} name="Potential Volume" />
                  <Area yAxisId="left" type="monotone" dataKey="observed_impressions" stroke="#3B82F6" strokeWidth={2.5} fillOpacity={1} fill="url(#colorObs)" name="Observed Volume" />
                  <Line yAxisId="right" type="monotone" dataKey="audience_risk" stroke="#EF4444" strokeWidth={2.5} dot={{ r: 2, fill: "#EF4444" }} name="Audience Risk" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Evidence Breakdown + Live Comments Stream */}
        <div className="space-y-6">
          {/* Risk Evidence Cards */}
          <div className="bg-white rounded-3xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <h3 className="font-bold text-slate-900 text-sm mb-3">Risk Evidence Signals</h3>

            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Harmful Weighted Share</span>
                  <span className="text-[10px] text-slate-400">Fractional weighted NLP count</span>
                </div>
                <span className="font-mono font-bold text-slate-900">0.48</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Wilson Lower Bound</span>
                  <span className="text-[10px] text-slate-400">95% statistical confidence floor</span>
                </div>
                <span className="font-mono font-bold text-slate-900">0.42</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Sentiment Decay</span>
                  <span className="text-[10px] text-slate-400">EWMA rolling rate</span>
                </div>
                <span className="font-mono font-bold text-[#DC2626]">0.61 (↑ 45%)</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Fatigue / Mockery Ratio</span>
                  <span className="text-[10px] text-slate-400">Repeated exposure tags</span>
                </div>
                <span className="font-mono font-bold text-[#DC2626]">0.55</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Comment Acceleration</span>
                  <span className="text-[10px] text-slate-400">Velocity slope (comments/min)</span>
                </div>
                <span className="font-mono font-bold text-[#D97706]">0.42</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Critical Complaint Rate</span>
                  <span className="text-[10px] text-slate-400">Severe product/service alerts</span>
                </div>
                <span className="font-mono font-bold text-slate-900">0.21</span>
              </div>
            </div>
          </div>

          {/* Live Comments Feed (Streamed) */}
          <div className="bg-white rounded-3xl p-5 border border-[#EAECEF] card-subtle-shadow">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-sm">Streamed Comments</h3>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">HMAC Anonymized</span>
            </div>

            <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
              {replay?.live_comments.map((cmt) => (
                <div key={cmt.event_id} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="w-5 h-5 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center font-bold text-[9px]">
                        {cmt.author_name ? cmt.author_name[0] : "U"}
                      </div>
                      <span className="font-semibold text-slate-900">{cmt.author_name || "User"}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getCategoryColor(cmt.category)}`}>
                      {cmt.category}
                    </span>
                  </div>

                  {/* Escaped safe text rendering */}
                  <p className="text-slate-700 text-xs leading-snug">{cmt.text}</p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span>Confidence: {(cmt.confidence * 100).toFixed(0)}%</span>
                    <span>{cmt.critical_complaint && "🚨 Critical Complaint"}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
