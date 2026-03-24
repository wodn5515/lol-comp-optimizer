import { create } from 'zustand';

export const usePlayerStore = create((set) => ({
  players: [],

  addPlayer: (player) =>
    set((state) => ({ players: [...state.players, player] })),

  removePlayer: (index) =>
    set((state) => ({
      players: state.players.filter((_, i) => i !== index),
    })),

  setPlayers: (players) => set({ players }),

  clearPlayers: () => set({ players: [] }),
}));
