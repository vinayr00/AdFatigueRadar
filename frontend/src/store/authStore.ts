import { create } from "zustand";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar: string;
  workspace: string;
  plan: string;
  token?: string;
  createdAt?: string;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  signup: (data: {
    fullName: string;
    email: string;
    organization: string;
    role: string;
    password?: string;
  }) => Promise<boolean>;
  logout: () => void;
}

// Check initial session in localStorage
const storedUser = localStorage.getItem("adfatigue_user");
let initialUser: UserProfile | null = null;
let initialAuth = false;

try {
  if (storedUser) {
    initialUser = JSON.parse(storedUser);
    initialAuth = true;
  }
} catch {
  // ignore
}

export const useAuthStore = create<AuthState>((set) => ({
  user: initialUser,
  isAuthenticated: initialAuth,

  login: async (email: string, _password?: string) => {
    // Simulate real auth call / network verification
    await new Promise((res) => setTimeout(res, 500));

    // Extract human-friendly name from email if not already present
    const prefix = email.split("@")[0] || "User";
    const formattedName = prefix
      .split(/[._-]/)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

    const initials = formattedName
      .split(" ")
      .map((n) => n.charAt(0))
      .join("")
      .slice(0, 2)
      .toUpperCase() || "AD";

    const userProfile: UserProfile = {
      id: `usr_${Date.now()}`,
      name: formattedName,
      email,
      role: "Lead Optimizer",
      avatar: initials,
      workspace: "AdFatigue Radar",
      plan: "Enterprise Pro",
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem("adfatigue_user", JSON.stringify(userProfile));
    set({ user: userProfile, isAuthenticated: true });
    return true;
  },

  signup: async (data) => {
    // Simulate signup API request
    await new Promise((res) => setTimeout(res, 600));

    const initials = data.fullName
      .trim()
      .split(" ")
      .map((n) => n.charAt(0))
      .join("")
      .slice(0, 2)
      .toUpperCase() || "AD";

    const userProfile: UserProfile = {
      id: `usr_${Date.now()}`,
      name: data.fullName.trim(),
      email: data.email.trim(),
      role: data.role || "Lead Optimizer",
      avatar: initials,
      workspace: data.organization.trim() || "AdFatigue Radar",
      plan: "Enterprise Pro",
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem("adfatigue_user", JSON.stringify(userProfile));
    set({ user: userProfile, isAuthenticated: true });
    return true;
  },

  logout: () => {
    localStorage.removeItem("adfatigue_user");
    set({ user: null, isAuthenticated: false });
  },
}));
