import { create } from "zustand";
import { CampaignState } from "../types/contracts";

interface ReplayUIState {
  isPlaying: boolean;
  speed: number;
  currentHour: number;
  scenarioSeed: number;
  scenarioName: string;
  selectedCampaignId: string;
  simulatedTime: string;
  currentState: CampaignState;
  setIsPlaying: (playing: boolean) => void;
  setSpeed: (speed: number) => void;
  setCurrentHour: (hour: number) => void;
  setScenarioSeed: (seed: number) => void;
  setScenarioName: (name: string) => void;
  setSelectedCampaignId: (id: string) => void;
  setCurrentState: (state: CampaignState) => void;
  resetReplay: () => void;
}

export const useReplayStore = create<ReplayUIState>((set) => ({
  isPlaying: false,
  speed: 1,
  currentHour: 38.5,
  scenarioSeed: 42,
  scenarioName: "Standard Fatigue Run (Seed #42)",
  selectedCampaignId: "cmp_summer_2024",
  simulatedTime: "2024-06-13T14:30:00Z",
  currentState: "WARNING",
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setSpeed: (speed) => set({ speed }),
  setCurrentHour: (hour) => set({ currentHour: hour }),
  setScenarioSeed: (seed) => set({ scenarioSeed: seed }),
  setScenarioName: (name) => set({ scenarioName: name }),
  setSelectedCampaignId: (id) => set({ selectedCampaignId: id }),
  setCurrentState: (state) => set({ currentState: state }),
  resetReplay: () => set({ currentHour: 0, isPlaying: false, currentState: "ACTIVE" }),
}));
