import React from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  Layers,
  PlaySquare,
  BarChart3,
  GitCompare,
  Bell,
  FileText,
  Settings,
} from "lucide-react";
import { useUIStore } from "../../store/uiStore";

interface NavItem {
  label: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { label: "Live Monitor", to: "/live-monitor", icon: Activity },
  { label: "Campaigns", to: "/campaigns", icon: Layers },
  { label: "Replay Studio", to: "/replay", icon: PlaySquare },
  { label: "Analytics", to: "/analytics", icon: BarChart3 },
  { label: "Comparisons", to: "/comparisons", icon: GitCompare },
  { label: "Alerts & Actions", to: "/alerts", icon: Bell },
  { label: "Audit Log", to: "/audit-log", icon: FileText },
  { label: "Settings", to: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen bg-[#F6F7F3] border-r border-[#E5E7EB] flex flex-col justify-between transition-all duration-300 ${
        sidebarOpen ? "w-64" : "w-20"
      }`}
    >
      {/* Brand Header */}
      <div className="p-5 pb-3">
        <NavLink to="/campaigns" className="flex items-start gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-[#E4EFE3] flex items-center justify-center shrink-0 border border-[#D0E2CF] group-hover:scale-105 transition-transform shadow-sm">
            {/* Organic Leaves Logo */}
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-[#2D5A3C]">
              <path
                d="M12 2C8 6 6 11 6 16C6 19.3137 8.68629 22 12 22C15.3137 22 18 19.3137 18 16C18 11 16 6 12 2Z"
                fill="#3F7A54"
                opacity="0.9"
              />
              <path
                d="M12 22V10M12 14L8 11M12 17L16 14"
                stroke="#FFFFFF"
                strokeWidth="1.75"
                strokeLinecap="round"
              />
              <circle cx="5" cy="9" r="3" fill="#88A98E" opacity="0.8" />
              <circle cx="19" cy="9" r="3" fill="#88A98E" opacity="0.8" />
            </svg>
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-[#111827] font-sans">
                AdFatigueRadar
              </span>
              <span className="text-[10px] text-[#6B7280] font-medium leading-tight mt-0.5">
                Catch Audience Fatigue<br />Before It Costs You
              </span>
            </div>
          )}
        </NavLink>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 group ${
                  isActive
                    ? "bg-[#E4EFE3] text-[#1E3A2B] font-semibold shadow-xs"
                    : "text-[#4B5563] hover:bg-[#EBEFE8] hover:text-[#1F2937]"
                } ${!sidebarOpen ? "justify-center px-2" : ""}`
              }
              title={!sidebarOpen ? item.label : undefined}
            >
              <Icon className="w-5 h-5 shrink-0 transition-transform group-hover:scale-110" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Botanical Banner (Matches Screenshot) */}
      {sidebarOpen ? (
        <div className="p-4 m-3 rounded-2xl bg-gradient-to-br from-[#E2ECE0] via-[#E8EFE5] to-[#F1DECE] border border-[#D5E2D2] relative overflow-hidden">
          {/* Subtle floral background SVG */}
          <div className="absolute right-0 bottom-0 opacity-40 pointer-events-none transform translate-x-3 translate-y-3">
            <svg width="120" height="120" viewBox="0 0 100 100" fill="none">
              <path
                d="M10 90 Q 40 40 80 20 Q 90 60 40 80 Z"
                fill="#2D5A3C"
              />
              <path
                d="M30 95 Q 60 70 85 40 Q 95 80 50 95 Z"
                fill="#D97706"
              />
              <circle cx="75" cy="25" r="12" fill="#E87042" opacity="0.6" />
            </svg>
          </div>
          <div className="relative z-10">
            <div className="font-serif text-sm font-bold text-[#1E3A2B] leading-snug">
              Healthy<br />
              Audiences<br />
              <span className="italic font-normal text-xs text-[#52796F]">and</span><br />
              Happier<br />
              Brands
            </div>
          </div>
        </div>
      ) : (
        <div className="p-3 flex justify-center text-xs text-emerald-800 font-serif">
          🌿
        </div>
      )}
    </aside>
  );
};
