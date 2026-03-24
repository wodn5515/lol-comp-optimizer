import { create } from 'zustand';

export const usePlayerFormStore = create((set) => ({
  matchCount: 15,
  errors: {},

  setMatchCount: (count) => set({ matchCount: count }),

  setError: (playerId, message) =>
    set((state) => ({
      errors: { ...state.errors, [playerId]: message },
    })),

  clearError: (playerId) =>
    set((state) => {
      const errors = { ...state.errors };
      delete errors[playerId];
      return { errors };
    }),

  clearAllErrors: () => set({ errors: {} }),

  validateRiotId: (value) => {
    if (!value.trim()) return '소환사명을 입력해주세요';
    const hashIndex = value.lastIndexOf('#');
    if (hashIndex === -1) return '이름#태그 형식으로 입력해주세요 (예: Hide on bush#KR1)';
    const gameName = value.slice(0, hashIndex);
    const tagLine = value.slice(hashIndex + 1);
    if (!gameName.trim()) return '게임 이름을 입력해주세요';
    if (!tagLine.trim()) return '태그라인을 입력해주세요 (# 뒤에 태그 입력)';
    return null;
  },
}));
