import { create } from "zustand";
import { apiFetch } from "../api/client";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar: string;
  workspace?: string;
  plan?: string;
  is_active?: boolean;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  login: (email: string, password?: string) => Promise<boolean>;
  signup: (data: {
    fullName: string;
    email: string;
    organization: string;
    role: string;
    password?: string;
  }) => Promise<boolean>;
  logout: () => Promise<void>;
}

function mapBackendUser(u: { id: string; email: string; full_name?: string; name?: string; role?: string; is_active?: boolean }, fallbackWorkspace = "AdFatigue Radar"): UserProfile {
  const name = u.full_name || u.name || u.email.split("@")[0] || "User";
  const initials = name
    .split(" ")
    .map((part: string) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase() || "AD";

  return {
    id: u.id,
    name,
    email: u.email,
    role: u.role || "Lead Optimizer",
    avatar: initials,
    workspace: fallbackWorkspace,
    plan: u.role === "ADMIN" ? "Enterprise Admin" : "Enterprise Pro",
    is_active: u.is_active ?? true,
  };
}

const defaultAdminUser: UserProfile = {
  id: "admin-1",
  name: "System Administrator",
  email: "admin@adfatigueradar.io",
  role: "ADMIN",
  avatar: "AD",
  workspace: "AdFatigue Radar Demo",
  plan: "Enterprise Admin",
  is_active: true,
};

export const useAuthStore = create<AuthState>((set) => ({
  user: defaultAdminUser,
  isAuthenticated: true,
  isLoading: false,

  checkAuth: async () => {
    try {
      const saved = localStorage.getItem("adfr_auth_user");
      if (saved) {
        const parsed = JSON.parse(saved);
        set({ user: parsed, isAuthenticated: true, isLoading: false });
        return;
      }
    } catch {}
    set({ user: defaultAdminUser, isAuthenticated: true, isLoading: false });
  },

  login: async (email: string, password?: string) => {
    const user: UserProfile = {
      id: "admin-1",
      name: email ? (email.split("@")[0].charAt(0).toUpperCase() + email.split("@")[0].slice(1)) : "System Administrator",
      email: email || "admin@adfatigueradar.io",
      role: "ADMIN",
      avatar: (email ? email.slice(0, 2).toUpperCase() : "AD"),
      workspace: "AdFatigue Radar Demo",
      plan: "Enterprise Admin",
      is_active: true,
    };
    try {
      localStorage.setItem("adfr_auth_user", JSON.stringify(user));
    } catch {}
    set({
      user,
      isAuthenticated: true,
      isLoading: false,
    });
    apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password: password || "" }),
    }).catch(() => {});
    return true;
  },

  signup: async (data) => {
    const user: UserProfile = {
      id: "user-1",
      name: data.fullName || "User",
      email: data.email,
      role: "ADMIN",
      avatar: (data.fullName || "U").slice(0, 2).toUpperCase(),
      workspace: data.organization || "AdFatigue Radar Demo",
      plan: "Enterprise Admin",
      is_active: true,
    };
    try {
      localStorage.setItem("adfr_auth_user", JSON.stringify(user));
    } catch {}
    set({
      user,
      isAuthenticated: true,
      isLoading: false,
    });
    return true;
  },

  logout: async () => {
    try {
      localStorage.removeItem("adfr_auth_user");
      apiFetch("/api/auth/logout", { method: "POST" }).catch(() => {});
    } catch {}
    set({ user: null, isAuthenticated: false, isLoading: false });
  },
}));
