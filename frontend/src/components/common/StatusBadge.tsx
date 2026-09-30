import React from "react";
import { CampaignState } from "../../types/contracts";

interface StatusBadgeProps {
  status: CampaignState | string;
  className?: string;
  size?: "sm" | "md";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = "", size = "md" }) => {
  const s = status.toUpperCase();

  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs";

  if (s === "WARNING") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] animate-pulse"></span>
        Warning
      </span>
    );
  }

  if (s === "ACTIVE") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#D1FAE5] text-[#059669] border border-[#A7F3D0] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#059669]"></span>
        Active
      </span>
    );
  }

  if (s === "PAUSED") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#DBEAFE] text-[#2563EB] border border-[#BFDBFE] ${sizeClasses} ${className}`}>
        <span className="font-mono text-[10px] leading-none">❚❚</span>
        Paused
      </span>
    );
  }

  if (s === "COMPLETED") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#EDE9FE] text-[#7C3AED] border border-[#DDD6FE] ${sizeClasses} ${className}`}>
        <span>✓</span>
        Completed
      </span>
    );
  }

  if (s === "SOFT_REDUCED") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#FFEDD5] text-[#C2410C] border border-[#FED7AA] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#C2410C]"></span>
        Soft Reduced (0.8x)
      </span>
    );
  }

  if (s === "BLOCKED") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]"></span>
        Blocked
      </span>
    );
  }

  if (s === "CRITICAL" || s === "OPEN") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]"></span>
        {status}
      </span>
    );
  }

  if (s === "INVESTIGATING") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#FFEDD5] text-[#EA580C] border border-[#FED7AA] ${sizeClasses} ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C] animate-pulse"></span>
        Investigating
      </span>
    );
  }

  if (s === "RESOLVED") {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-[#D1FAE5] text-[#059669] border border-[#A7F3D0] ${sizeClasses} ${className}`}>
        <span>✓</span>
        Resolved
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-slate-100 text-slate-700 border border-slate-200 ${sizeClasses} ${className}`}>
      {status}
    </span>
  );
};
