import React from "react";
import { formatRiskScore } from "../../lib/formatters";

interface RiskBadgeProps {
  score: number | null | undefined;
  className?: string;
  showDot?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score, className = "", showDot = true }) => {
  if (score === null || score === undefined || isNaN(score)) {
    return <span className={`text-slate-400 text-sm ${className}`}>N/A</span>;
  }

  let dotColor = "bg-[#10B981]";
  let textColor = "text-slate-800";

  if (score >= 0.65) {
    dotColor = "bg-[#EF4444]";
    textColor = "text-[#DC2626] font-semibold";
  } else if (score >= 0.40) {
    dotColor = "bg-[#F59E0B]";
    textColor = "text-[#D97706] font-medium";
  } else {
    dotColor = "bg-[#10B981]";
    textColor = "text-[#059669] font-medium";
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-sm ${textColor} ${className}`}>
      {showDot && <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>}
      <span>{formatRiskScore(score)}</span>
    </span>
  );
};
