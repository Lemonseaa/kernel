import { create } from "zustand";
import { getApiToken, setApiToken } from "../api/client";

type UiState = {
  selectedScenarioId: string;
  token: string;
  setSelectedScenarioId: (scenarioId: string) => void;
  setToken: (token: string) => void;
};

export const useUiStore = create<UiState>((set) => ({
  selectedScenarioId: "",
  token: getApiToken(),
  setSelectedScenarioId: (scenarioId) => set({ selectedScenarioId: scenarioId }),
  setToken: (token) => {
    setApiToken(token);
    set({ token });
  }
}));
