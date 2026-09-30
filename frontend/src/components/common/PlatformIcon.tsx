import React from "react";
import { Platform } from "../../types/contracts";

interface PlatformIconProps {
  platform: Platform | string;
  className?: string;
  size?: number;
}

export const PlatformIcon: React.FC<PlatformIconProps> = ({ platform, className = "w-5 h-5", size = 20 }) => {
  const p = platform.toLowerCase();

  if (p.includes("meta") || p.includes("facebook") || p === "meta") {
    return (
      <span className={`inline-flex items-center justify-center text-[#0668E1] ${className}`} title="Meta Ads">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 8c-3 0-5 2.5-5 5.5 0 3 2.5 5 5 5 2.5 0 4-2.5 5-5 1 2.5 2.5 5 5 5 2.5 0 5-2 5-5 0-3-2-5.5-5-5.5-3 0-4.5 3-5 5-.5-2-2-5-5-5z" />
        </svg>
      </span>
    );
  }

  if (p.includes("google") || p === "google") {
    return (
      <span className={`inline-flex items-center justify-center text-[#4285F4] ${className}`} title="Google Ads">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14.93V19h-2v-2.07c-2.84-.48-4.5-2.34-4.5-4.43h2.1c0 1.25 1.05 2.5 3.4 2.5 1.95 0 3-.95 3-2.15 0-1.4-1.15-2-3.1-2.45C9 9.8 7 9 7 6.85 7 4.9 8.7 3.5 11 3.07V1h2v2.07c2.4.45 3.9 2.05 4 4.03h-2.1c-.15-1.15-1-2.1-2.9-2.1-1.7 0-2.8.85-2.8 1.95 0 1.25 1 1.8 2.95 2.25 2.95.7 5.05 1.55 5.05 3.83 0 2.1-1.75 3.55-4.2 3.93z"/>
        </svg>
      </span>
    );
  }

  if (p.includes("tiktok") || p === "tiktok") {
    return (
      <span className={`inline-flex items-center justify-center text-[#111111] ${className}`} title="TikTok Ads">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298-.002.595.042.88.13V9.4a6.33 6.33 0 0 0-.88-.06A6.34 6.34 0 0 0 3.14 15.7a6.34 6.34 0 0 0 10.82 4.48 6.28 6.28 0 0 0 1.87-4.51V8.71a8.28 8.28 0 0 0 4.76 1.48v-3.5z"/>
        </svg>
      </span>
    );
  }

  if (p.includes("youtube") || p === "youtube") {
    return (
      <span className={`inline-flex items-center justify-center text-[#FF0000] ${className}`} title="YouTube Ads">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
          <path d="M21.58 7.19a2.5 2.5 0 0 0-1.76-1.77C18.26 5 12 5 12 5s-6.26 0-7.82.42A2.5 2.5 0 0 0 2.42 7.19 26.24 26.24 0 0 0 2 12a26.24 26.24 0 0 0 .42 4.81 2.5 2.5 0 0 0 1.76 1.77C5.74 19 12 19 12 19s6.26 0 7.82-.42a2.5 2.5 0 0 0 1.76-1.77A26.24 26.24 0 0 0 22 12a26.24 26.24 0 0 0-.42-4.81zM9.75 15.02V8.98L15.5 12l-5.75 3.02z" />
        </svg>
      </span>
    );
  }

  if (p.includes("x") || p.includes("twitter")) {
    return (
      <span className={`inline-flex items-center justify-center text-[#0F1419] ${className}`} title="X Ads">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      </span>
    );
  }

  if (p.includes("slack")) {
    return (
      <span className={`inline-flex items-center justify-center text-[#4A154B] ${className}`} title="Slack">
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
          <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52-2.523c0-1.393 1.128-2.52 2.52-2.52h2.52v2.52c0 1.395-1.128 2.523-2.52 2.523zm3.784-2.523c0-1.393 1.128-2.52 2.521-2.52 1.392 0 2.52 1.127 2.52 2.52v6.307a2.528 2.528 0 0 1-2.52 2.524 2.528 2.528 0 0 1-2.521-2.524v-6.307zM8.826 5.042a2.528 2.528 0 0 1 2.521-2.52c1.392 0 2.52 1.127 2.52 2.52v2.52h-2.52a2.528 2.528 0 0 1-2.521-2.52zm2.521 3.784c1.392 0 2.52 1.128 2.52 2.521 0 1.392-1.128 2.52-2.52 2.52H2.52A2.528 2.528 0 0 1 0 11.347c0-1.393 1.128-2.521 2.52-2.521h8.827z"/>
        </svg>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center justify-center text-slate-500 ${className}`}>
      🌐
    </span>
  );
};
