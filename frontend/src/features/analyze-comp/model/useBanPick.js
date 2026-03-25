import { create } from 'zustand';

const initialState = {
  analyzedPlayers: [],
  bannedChampions: [],
  enemyPicks: [],
  lockedPicks: {},
  lockedPositions: {},   // {"playerKey": "TOP"}
  recommendations: [],
  isOptimizing: false,
};

export const useBanPickStore = create((set) => ({
  ...initialState,

  setAnalyzedPlayers: (players) => set({ analyzedPlayers: players }),

  addBan: (championName) =>
    set((state) => {
      if (state.bannedChampions.includes(championName)) return state;
      if (state.bannedChampions.length >= 10) return state;
      return { bannedChampions: [...state.bannedChampions, championName] };
    }),

  removeBan: (championName) =>
    set((state) => ({
      bannedChampions: state.bannedChampions.filter((c) => c !== championName),
    })),

  addEnemyPick: (championName) =>
    set((state) => {
      if (state.enemyPicks.includes(championName)) return state;
      if (state.enemyPicks.length >= 5) return state;
      return { enemyPicks: [...state.enemyPicks, championName] };
    }),

  removeEnemyPick: (championName) =>
    set((state) => ({
      enemyPicks: state.enemyPicks.filter((c) => c !== championName),
    })),

  lockPick: (playerKey, championName) =>
    set((state) => ({
      lockedPicks: { ...state.lockedPicks, [playerKey]: championName },
    })),

  unlockPick: (playerKey) =>
    set((state) => {
      const lockedPicks = { ...state.lockedPicks };
      delete lockedPicks[playerKey];
      return { lockedPicks };
    }),

  lockPosition: (playerKey, lane) =>
    set((state) => ({
      lockedPositions: { ...state.lockedPositions, [playerKey]: lane },
    })),

  unlockPosition: (playerKey) =>
    set((state) => {
      const lockedPositions = { ...state.lockedPositions };
      delete lockedPositions[playerKey];
      return { lockedPositions };
    }),

  setRecommendations: (recs) => set({ recommendations: recs }),

  setIsOptimizing: (v) => set({ isOptimizing: v }),

  reset: () => set(initialState),
}));
