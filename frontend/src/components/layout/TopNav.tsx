import React, { useState } from "react";
import { Search, Bell, Play, ChevronDown, Menu, CheckCircle2, ShieldCheck, AlertTriangle, LogOut, User } from "lucide-react";
import { useUIStore } from "../../store/uiStore";
import { useReplayStore } from "../../store/replayStore";
import { useAuthStore } from "../../store/authStore";
import { useNavigate } from "react-router-dom";

export const TopNav: React.FC = () => {
  const { sidebarOpen, toggleSidebar, globalSearch, setGlobalSearch } = useUIStore();
  const { isPlaying, setIsPlaying, speed, setSpeed, currentHour, scenarioName } = useReplayStore();
  const { user, logout } = useAuthStore();
  const [replayMenuOpen, setReplayMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 h-16 bg-[#F8F9FA] border-b border-[#EAECEF] px-6 flex items-center justify-between gap-4">
      {/* Left: Sidebar Toggle & Search Input */}
      <div className="flex items-center gap-4 flex-1 max-w-2xl">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-xl text-slate-500 hover:bg-slate-200 transition-colors"
          title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={globalSearch}
            onChange={(e) => setGlobalSearch(e.target.value)}
            placeholder="Search campaigns, keywords, or comments..."
            className="w-full pl-10 pr-4 py-2 text-sm bg-[#FFFFFF] border border-[#E2E8F0] rounded-full focus:outline-none focus:ring-2 focus:ring-[#2D5A3C] focus:border-transparent placeholder:text-slate-400 transition-all card-subtle-shadow"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 relative">
        {/* Replay Mode Dropdown Button */}
        <div className="relative">
          <button
            onClick={() => setReplayMenuOpen(!replayMenuOpen)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1E3A2B] text-white text-xs font-semibold hover:bg-[#284E3A] transition-all shadow-sm"
          >
            <div className="w-4 h-4 rounded-full bg-[#34D399] text-[#1E3A2B] flex items-center justify-center">
              <Play className="w-2.5 h-2.5 fill-current ml-0.5" />
            </div>
            <span>Replay Mode</span>
            <ChevronDown className="w-3.5 h-3.5 text-emerald-200" />
          </button>

          {replayMenuOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl border border-slate-200 shadow-xl p-3 z-50 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Replay Controls</span>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                  {isPlaying ? "RUNNING" : "PAUSED"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-3">{scenarioName}</p>
              <div className="flex items-center justify-between gap-2 mb-3 bg-slate-50 p-2 rounded-xl text-xs">
                <span className="text-slate-600">Time:</span>
                <span className="font-mono font-semibold text-slate-800">Hour {currentHour.toFixed(1)} / 72</span>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="flex-1 py-1.5 px-3 rounded-xl bg-[#2D5A3C] text-white text-xs font-medium hover:bg-[#1E3A2B] transition-colors flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3 h-3" />
                  {isPlaying ? "Pause Replay" : "Start Replay"}
                </button>
                <button
                  onClick={() => navigate("/replay")}
                  className="py-1.5 px-3 rounded-xl bg-slate-100 text-slate-700 text-xs font-medium hover:bg-slate-200 transition-colors"
                >
                  Open Studio
                </button>
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
                <span>Speed Multiplier:</span>
                <div className="flex gap-1">
                  {[1, 5, 10, 60].map((s) => (
                    <button
                      key={s}
                      onClick={() => setSpeed(s)}
                      className={`px-1.5 py-0.5 rounded text-[11px] font-semibold ${speed === s ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                        }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Notifications Icon with Badge */}
        <div className="relative">
          <button
            onClick={() => setNotificationOpen(!notificationOpen)}
            className="p-2 rounded-full text-slate-600 hover:bg-slate-200 relative transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-red-500 ring-2 ring-[#F8F9FA]"></span>
          </button>

          {notificationOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-slate-200 shadow-xl p-4 z-50 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Alerts & Notifications</h4>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-semibold">1 Critical</span>
              </div>
              <div className="space-y-2.5">
                <div
                  onClick={() => {
                    navigate("/alerts");
                    setNotificationOpen(false);
                  }}
                  className="p-2.5 rounded-xl bg-red-50 border border-red-100 cursor-pointer hover:bg-red-100 transition-colors"
                >
                  <div className="flex items-center gap-2 text-xs font-semibold text-red-800">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                    Summer Collection 2024
                  </div>
                  <p className="text-[11px] text-red-700 mt-1">Audience fatigue crossed warning threshold (0.65)</p>
                  <span className="text-[10px] text-red-500 font-medium">2 min ago</span>
                </div>
                <div
                  onClick={() => {
                    navigate("/alerts");
                    setNotificationOpen(false);
                  }}
                  className="p-2.5 rounded-xl bg-amber-50 border border-amber-100 cursor-pointer hover:bg-amber-100 transition-colors"
                >
                  <div className="flex items-center gap-2 text-xs font-semibold text-amber-800">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    Monsoon Sale
                  </div>
                  <p className="text-[11px] text-amber-700 mt-1">Negative sentiment spike detected</p>
                  <span className="text-[10px] text-amber-500 font-medium">12 min ago</span>
                </div>
              </div>
              <button
                onClick={() => {
                  navigate("/alerts");
                  setNotificationOpen(false);
                }}
                className="w-full mt-3 py-1.5 text-xs text-center font-medium text-emerald-800 hover:text-emerald-900"
              >
                View all alerts →
              </button>
            </div>
          )}
        </div>

        {/* User Account / Profile */}
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full hover:bg-slate-200 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-[#B45309] text-white flex items-center justify-center text-xs font-bold shadow-xs">
              {user?.avatar || "AD"}
            </div>
            <div className="text-left hidden md:block">
              <div className="text-xs font-bold text-slate-800 leading-tight">{user?.name || "AdFatigue Radar"}</div>
              <div className="text-[10px] text-slate-500">{user?.role || "Demo Account"}</div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-60 bg-white rounded-2xl border border-slate-200 shadow-xl p-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-800">{user?.name || "Aditya Sharma"}</p>
                <p className="text-[11px] text-slate-500">{user?.email || "demo@adfatigueradar.com"}</p>
                <span className="inline-block mt-1 text-[10px] font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  {user?.role || "Lead Optimizer"}
                </span>
              </div>
              <button
                onClick={() => {
                  navigate("/settings");
                  setUserMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-xl transition-colors mt-1"
              >
                Workspace Settings
              </button>
              <button
                onClick={() => {
                  navigate("/audit-log");
                  setUserMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Audit Logs
              </button>
              <button
                onClick={() => {
                  navigate("/login");
                  setUserMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Switch User / Login
              </button>
              <div className="my-1 border-t border-slate-100"></div>
              <div className="px-3 py-1.5 text-[11px] text-emerald-700 flex items-center gap-1.5 font-medium">
                <ShieldCheck className="w-3.5 h-3.5" />
                Sandbox Mode Protected
              </div>
              <div className="my-1 border-t border-slate-100"></div>
              <button
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 text-xs font-bold text-red-600 hover:bg-red-50 rounded-xl transition-colors flex items-center gap-2"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

