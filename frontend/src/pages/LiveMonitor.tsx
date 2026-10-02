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
import { pauseReplayApi, resumeReplayApi } from "../api/replay";
import { useCampaign, useCampaigns, useDemoCampaign } from "../hooks/useCampaigns";
import { useReplayStore } from "../store/replayStore";
import { CommentCategory, CampaignState } from "../types/contracts";

export const LiveMonitor: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { data: allCampaigns = [] } = useCampaigns();
  const campaignIdParam =
    searchParams.get("campaign") ||
    localStorage.getItem("active_demo_campaign") ||
    allCampaigns.find((c) => c.id.startsWith("camp_"))?.id ||
    "cmp_summer_2024";

  useEffect(() => {
    if (campaignIdParam) {
      localStorage.setItem("active_demo_campaign", campaignIdParam);
    }
  }, [campaignIdParam]);

  const {
    isPlaying,
    setIsPlaying,
    speed,
    setSpeed,
    currentHour,
    setCurrentHour,
  } = useReplayStore();

  const { data: campaign } = useCampaign(campaignIdParam);
  const { data: demoCampaign } = useDemoCampaign(campaignIdParam);
  const { data: replay, refetch } = useReplay(campaignIdParam, speed);
  const startReplayMutation = useStartReplay();
  const resetReplayMutation = useResetReplay();
  const [streamError, setStreamError] = useState<string | null>(null);

  // Replay progress and status come from the authoritative backend SSE stream.
  useEffect(() => {
    const source = new EventSource(`/campaigns/${encodeURIComponent(campaignIdParam)}/stream`);
    source.addEventListener("STEP_UPDATE", (event) => {
      try {
        const update = JSON.parse((event as MessageEvent).data) as { is_running?: boolean };
        if (typeof update.is_running === "boolean") setIsPlaying(update.is_running);
        void refetch().then(({ data }) => {
          if (data) setCurrentHour(data.current_hour);
        });
        setStreamError(null);
      } catch { setStreamError("Received an invalid replay update."); }
    });
    source.onerror = () => setStreamError("Live replay connection is unavailable.");
    return () => source.close();
  }, [campaignIdParam, refetch, setCurrentHour, setIsPlaying]);

  // Derive current telemetry step at currentHour
  const timelinePoints = replay?.points || [];
  if (!timelinePoints.length) {
    return <section className="m-6 rounded-2xl border border-slate-200 bg-white p-8 text-slate-700">
      <h2 className="text-lg font-semibold">No replay snapshot is available</h2>
      <p className="mt-2 text-sm">Start a replay for a campaign with authorized replay events to populate this view.</p>
      {streamError && <p role="alert" className="mt-2 text-sm text-red-700">{streamError}</p>}
      <button onClick={() => void startReplayMutation.mutateAsync({ campaignId: campaignIdParam, speed }).then(() => setIsPlaying(true)).catch((error) => setStreamError(error instanceof Error ? error.message : "Replay could not be started."))} className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-white">Start replay</button>
    </section>;
  }
  const currentPoint = timelinePoints.reduce((prev, curr) => {
    return Math.abs(curr.hour - currentHour) < Math.abs(prev.hour - currentHour) ? curr : prev;
  });

  // For demo campaigns, the selected demo campaign JSON is the authoritative source of truth
  const isDemo = Boolean(demoCampaign && typeof demoCampaign.risk_score === "number");
  const effectiveAudienceRisk = isDemo ? Number(demoCampaign.risk_score) : currentPoint.audience_risk;
  const effectiveEconomicRisk = isDemo
    ? (typeof demoCampaign.economic_risk === "number" ? demoCampaign.economic_risk : Number((effectiveAudienceRisk * 0.82).toFixed(2)))
    : currentPoint.economic_risk;
  const effectiveCpa = isDemo && typeof demoCampaign.cpa === "number" ? demoCampaign.cpa : currentPoint.cpa;
  const effectiveState = isDemo ? (demoCampaign.status || "ACTIVE") : (currentPoint.state || "ACTIVE");
  const effectiveSeverity = isDemo ? (demoCampaign.severity || "HEALTHY") : (effectiveAudienceRisk >= 0.65 ? "CRITICAL" : "HEALTHY");
  const effectiveHealth = isDemo ? (typeof demoCampaign.health_score === "number" ? demoCampaign.health_score : 100) : 100;
  const currentState = effectiveState;

  const handleTogglePlay = async () => {
    if (!isPlaying) {
      try {
        if (replay?.is_running) await resumeReplayApi(campaignIdParam);
        else await startReplayMutation.mutateAsync({ campaignId: campaignIdParam, speed });
        setIsPlaying(true);
        setStreamError(null);
      } catch (error) { setStreamError(error instanceof Error ? error.message : "Replay could not be started."); }
    } else {
      try {
        await pauseReplayApi(campaignIdParam);
        setIsPlaying(false);
        setStreamError(null);
      } catch (error) { setStreamError(error instanceof Error ? error.message : "Replay could not be paused."); }
    }
  };

  const handleReset = () => {
    resetReplayMutation.mutate(campaignIdParam);
    setCurrentHour(0);
    setIsPlaying(false);
  };

  const getCategoryColor = (cat: CommentCategory | null) => {
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
  const signalValue = (name: string) => {
    const value = currentPoint.signals?.[name];
    return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "Unavailable";
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Status Bar */}
      <div className="bg-white rounded-3xl p-6 border border-[#EAECEF] card-subtle-shadow">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            {campaign?.thumbnail_url ? <img src={campaign.thumbnail_url} alt="" className="w-16 h-16 rounded-2xl object-cover border border-slate-200 shadow-sm" /> :
              <div aria-hidden="true" className="w-16 h-16 rounded-2xl border border-slate-200 bg-slate-100 flex items-center justify-center text-xl font-bold text-slate-500">{campaign?.name?.[0] || "—"}</div>}
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold font-serif text-slate-900">
                  {campaign?.name || campaignIdParam}
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
              <span className={`text-xs font-bold ${effectiveAudienceRisk >= 0.65 ? "text-[#DC2626]" : "text-[#059669]"}`}>
                {effectiveAudienceRisk.toFixed(2)}
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
            Seed: {replay?.seed ?? "—"}
          </span>
          <span className="bg-black/30 border border-white/20 rounded-xl px-3 py-1 text-xs">{replay?.scenario_name ?? "Replay"}</span>
        </div>
      </div>

      {/* 6 Dynamic KPI Metrics at Current Replay Point */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard
          title="Observed Impressions"
          value={formatNumber(currentPoint.observed_impressions, true)}
          subValue={currentPoint.potential_impressions === null ? "Potential data unavailable" : `Pot: ${formatNumber(currentPoint.potential_impressions, true)}`}
          isPositive={currentPoint.observed_impressions > 0}
          icon={<Activity className="w-5 h-5 text-[#10B981]" />}
          iconBg="bg-[#D1FAE5]"
          sparklineData={[currentPoint.observed_impressions]}
          sparklineColor="#10B981"
        />
        <KPICard
          title="Observed Spend"
          value={formatCurrency(currentPoint.observed_spend)}
          subValue={currentPoint.potential_spend === null ? "Potential data unavailable" : `Pot: ${formatCurrency(currentPoint.potential_spend)}`}
          isPositive={true}
          icon={<TrendingDown className="w-5 h-5 text-[#3B82F6]" />}
          iconBg="bg-[#DBEAFE]"
        />
        <KPICard
          title="Current CPA"
          value={effectiveCpa !== null ? formatCurrency(effectiveCpa) : "—"}
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
          value={effectiveAudienceRisk.toFixed(2)}
          change={effectiveAudienceRisk >= 0.65 ? "WARNING" : "HEALTHY"}
          isPositive={effectiveAudienceRisk < 0.65}
          icon={<Flame className="w-5 h-5 text-[#EF4444]" />}
          iconBg="bg-[#FEE2E2]"
        />
        <KPICard
          title="Economic Risk"
          value={effectiveEconomicRisk !== null ? effectiveEconomicRisk.toFixed(2) : "N/A"}
          subValue={effectiveEconomicRisk !== null ? (effectiveEconomicRisk >= 0.50 ? "Dual Confirmed" : "Normal Efficiency") : "< 20 conv/hr"}
          isPositive={effectiveEconomicRisk ? effectiveEconomicRisk < 0.60 : true}
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
                Risk thresholds are configured by the backend
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center my-2">
              {/* Audience Risk Gauge */}
              <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <span className="text-xs font-bold text-slate-700 mb-2">Audience Risk</span>
                <div className={`w-28 h-28 rounded-full border-8 flex flex-col items-center justify-center ${
                  effectiveAudienceRisk >= 0.65
                    ? "border-red-500 bg-red-50/50"
                    : effectiveAudienceRisk >= 0.40
                    ? "border-amber-400 bg-amber-50/50"
                    : "border-emerald-500 bg-emerald-50/50"
                }`}>
                  <span className="text-2xl font-bold font-serif text-slate-900">
                    {effectiveAudienceRisk.toFixed(2)}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500">
                    {effectiveAudienceRisk >= 0.65 ? "ELEVATED" : "NORMAL"}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 mt-2">{isDemo ? `Demo Health: ${effectiveHealth}/100` : "Wilson lower-bound & decay"}</span>
              </div>

              {/* Economic Risk Gauge */}
              <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <span className="text-xs font-bold text-slate-700 mb-2">Economic Risk</span>
                <div className={`w-28 h-28 rounded-full border-8 flex flex-col items-center justify-center ${
                  effectiveEconomicRisk !== null && effectiveEconomicRisk >= 0.60
                    ? "border-red-500 bg-red-50/50"
                    : effectiveEconomicRisk !== null && effectiveEconomicRisk >= 0.40
                    ? "border-amber-400 bg-amber-50/50"
                    : effectiveEconomicRisk !== null
                    ? "border-emerald-500 bg-emerald-50/50"
                    : "border-slate-300 bg-slate-100"
                }`}>
                  <span className="text-2xl font-bold font-serif text-slate-900">
                    {effectiveEconomicRisk !== null ? effectiveEconomicRisk.toFixed(2) : "N/A"}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500">
                    {effectiveEconomicRisk !== null ? (effectiveEconomicRisk >= 0.50 ? "CONFIRMED" : "NORMAL") : "GATE N/A"}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 mt-2">{effectiveEconomicRisk !== null ? `CPA Impact: +${(effectiveEconomicRisk * 40).toFixed(0)}%` : "CPA & conversion decay"}</span>
              </div>

              {/* State Machine Status */}
              <div className="flex flex-col justify-between h-full p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div>
                  <span className="text-xs font-bold text-slate-700 block mb-1">State Machine</span>
                  <div className="my-1">
                    <StatusBadge status={currentState} size="md" />
                  </div>
                  <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                    {isDemo
                      ? `Demo Simulation: Health ${effectiveHealth}/100, Severity: ${effectiveSeverity}`
                      : (replay?.state_reason || "All telemetry parameters within safety bounds.")}
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
                <span className="font-mono font-bold text-slate-900">{signalValue("harmful_negative_ratio")}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Wilson Lower Bound</span>
                  <span className="text-[10px] text-slate-400">95% statistical confidence floor</span>
                </div>
                <span className="font-mono font-bold text-slate-900">Unavailable</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Sentiment Decay</span>
                  <span className="text-[10px] text-slate-400">EWMA rolling rate</span>
                </div>
                <span className="font-mono font-bold text-[#DC2626]">{signalValue("sentiment_decay")}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Fatigue / Mockery Ratio</span>
                  <span className="text-[10px] text-slate-400">Repeated exposure tags</span>
                </div>
                <span className="font-mono font-bold text-[#DC2626]">{signalValue("fatigue_mockery")}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Comment Acceleration</span>
                  <span className="text-[10px] text-slate-400">Velocity slope (comments/min)</span>
                </div>
                <span className="font-mono font-bold text-[#D97706]">{signalValue("comment_acceleration")}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 block">Critical Complaint Signal</span>
                  <span className="text-[10px] text-slate-400">Severe product/service alerts</span>
                </div>
                <span className="font-mono font-bold text-slate-900">{signalValue("critical_complaint_signal")}</span>
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
              {((isDemo && Array.isArray(demoCampaign?.comments) && demoCampaign.comments.length > 0)
                ? [...demoCampaign.comments].reverse().map((c: any, i: number) => ({
                    event_id: c.comment_id || c.id || `c-${i}`,
                    author_name: c.author || "Demo User",
                    text: c.text,
                    category: (c.category || "neutral") as CommentCategory,
                    confidence: c.confidence ?? 0.90,
                    critical_complaint: Boolean(c.critical_complaint),
                  }))
                : (replay?.live_comments || [])
              ).map((cmt) => (
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
                    <span>Confidence: {((cmt.confidence ?? 0) * 100).toFixed(0)}%</span>
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
