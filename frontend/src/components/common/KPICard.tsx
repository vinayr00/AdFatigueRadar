import React from "react";
import { Sparkline } from "./Sparkline";

export interface KPICardProps {
  title: string;
  value: string | number;
  subValue?: string;
  change?: string | number;
  isPositive?: boolean;
  icon?: React.ReactNode;
  iconBg?: string;
  sparklineData?: number[];
  sparklineColor?: string;
  className?: string;
  onClick?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subValue,
  change,
  isPositive = true,
  icon,
  iconBg = "bg-emerald-50 text-emerald-600",
  sparklineData,
  sparklineColor = "#10B981",
  className = "",
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl p-4 border border-[#EAECEF] card-subtle-shadow card-hover-shadow flex flex-col justify-between relative overflow-hidden ${
        onClick ? "cursor-pointer hover:border-slate-300" : ""
      } ${className}`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-3">
          {icon && (
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
              {icon}
            </div>
          )}
          <div>
            <div className="text-2xl font-bold text-[#1E293B] tracking-tight">{value}</div>
            <div className="text-xs font-medium text-[#64748B]">{title}</div>
          </div>
        </div>
      </div>

      {(sparklineData || change !== undefined || subValue) && (
        <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-50">
          {sparklineData ? (
            <Sparkline data={sparklineData} color={sparklineColor} width={75} height={20} />
          ) : (
            <div />
          )}

          {change !== undefined && (
            <span
              className={`text-xs font-semibold inline-flex items-center gap-0.5 ${
                isPositive ? "text-[#059669]" : "text-[#DC2626]"
              }`}
            >
              {isPositive ? "↑" : "↓"} {typeof change === "number" ? `${change > 0 ? "+" : ""}${change}%` : change}
            </span>
          )}

          {subValue && !change && (
            <span className="text-xs font-medium text-slate-500">{subValue}</span>
          )}
        </div>
      )}
    </div>
  );
};
