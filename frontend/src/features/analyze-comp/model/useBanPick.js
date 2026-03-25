import { create } from 'zustand';
import { saveSession, loadSession, clearSession } from '../../../shared/lib/sessionPersistence';

const initialState = {
  analyzedPlayers: [],
  bannedChampions: [],
  enemyPicks: [],
  lockedPicks: {},
  lockedPositions: {},   // {"playerKey": "TOP"}
  recommendations: [],
  isOptimizing: false,
};

function persistToSession(state) {
  if (state.analyzedPlayers.length === 0) return;
  saveSession({
    players: state.analyzedPlayers,
    banned_champions: state.bannedChampions,
    enemy_picks: state.enemyPicks,
    locked_picks: state.lockedPicks,
    locked_positions: state.lockedPositions,
  });
}

export const useBanPickStore = create((set, get) => ({
  ...initialState,

  setAnalyzedPlayers: (players) =>
    set((state) => {
      const next = { ...state, analyzedPlayers: players };
      persistToSession(next);
      return { analyzedPlayers: players };
    }),

  addBan: (championName) =>
    set((state) => {
      if (state.bannedChampions.includes(championName)) return state;
      if (state.bannedChampions.length >= 10) return state;
      const next = { ...state, bannedChampions: [...state.bannedChampions, championName] };
      persistToSession(next);
      return { bannedChampions: next.bannedChampions };
    }),

  removeBan: (championName) =>
    set((state) => {
      const bannedChampions = state.bannedChampions.filter((c) => c !== championName);
      const next = { ...state, bannedChampions };
      persistToSession(next);
      return { bannedChampions };
    }),

  addEnemyPick: (championName) =>
    set((state) => {
      if (state.enemyPicks.includes(championName)) return state;
      if (state.enemyPicks.length >= 5) return state;
      const next = { ...state, enemyPicks: [...state.enemyPicks, championName] };
      persistToSession(next);
      return { enemyPicks: next.enemyPicks };
    }),

  removeEnemyPick: (championName) =>
    set((state) => {
      const enemyPicks = state.enemyPicks.filter((c) => c !== championName);
      const next = { ...state, enemyPicks };
      persistToSession(next);
      return { enemyPicks };
    }),

  lockPick: (playerKey, championName) =>
    set((state) => {
      const lockedPicks = { ...state.lockedPicks, [playerKey]: championName };
      const next = { ...state, lockedPicks };
      persistToSession(next);
      return { lockedPicks };
    }),

  unlockPick: (playerKey) =>
    set((state) => {
      const lockedPicks = { ...state.lockedPicks };
      delete lockedPicks[playerKey];
      const next = { ...state, lockedPicks };
      persistToSession(next);
      return { lockedPicks };
    }),

  lockPosition: (playerKey, lane) =>
    set((state) => {
      const lockedPositions = { ...state.lockedPositions, [playerKey]: lane };
      const next = { ...state, lockedPositions };
      persistToSession(next);
      return { lockedPositions };
    }),

  unlockPosition: (playerKey) =>
    set((state) => {
      const lockedPositions = { ...state.lockedPositions };
      delete lockedPositions[playerKey];
      const next = { ...state, lockedPositions };
      persistToSession(next);
      return { lockedPositions };
    }),

  setRecommendations: (recs) => set({ recommendations: recs }),

  setIsOptimizing: (v) => set({ isOptimizing: v }),

  reset: () => {
    clearSession();
    set(initialState);
  },

  hydrateFromSession: () => {
    const session = loadSession();
    if (!session) return false;
    if (!session.players || session.players.length === 0) return false;

    set({
      analyzedPlayers: session.players,
      bannedChampions: session.banned_champions || [],
      enemyPicks: session.enemy_picks || [],
      lockedPicks: session.locked_picks || {},
      lockedPositions: session.locked_positions || {},
    });
    return true;
  },
}));
