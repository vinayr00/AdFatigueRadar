import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  globalSearch: string;
  setGlobalSearch: (q: string) => void;
  selectedCampaignId: string;
  setSelectedCampaignId: (id: string) => void;
  dateRange: string;
  setDateRange: (range: string) => void;
  replayModeOpen: boolean;
  setReplayModeOpen: (open: boolean) => void;
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
  createCampaignModalOpen: boolean;
  setCreateCampaignModalOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  globalSearch: "",
  setGlobalSearch: (q) => set({ globalSearch: q }),
  selectedCampaignId: "cmp_summer_2024",
  setSelectedCampaignId: (id) => set({ selectedCampaignId: id }),
  dateRange: "Jun 01, 2024 – Jun 30, 2024",
  setDateRange: (range) => set({ dateRange: range }),
  replayModeOpen: false,
  setReplayModeOpen: (open) => set({ replayModeOpen: open }),
  notificationsOpen: false,
  setNotificationsOpen: (open) => set({ notificationsOpen: open }),
  createCampaignModalOpen: false,
  setCreateCampaignModalOpen: (open) => set({ createCampaignModalOpen: open }),
}));
