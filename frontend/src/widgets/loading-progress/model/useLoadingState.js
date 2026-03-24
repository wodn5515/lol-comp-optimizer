import { create } from 'zustand';

const STAGES = [
  { id: 'fetch', label: '플레이어 정보 조회 중...', weight: 30 },
  { id: 'analyze', label: '전적 분석 중...', weight: 50 },
  { id: 'optimize', label: '조합 최적화 중...', weight: 20 },
];

export const useLoadingStateStore = create((set, get) => ({
  isActive: false,
  currentStageIndex: 0,
  progress: 0,
  stages: STAGES,
  completedPlayers: [],

  startLoading: () =>
    set({
      isActive: true,
      currentStageIndex: 0,
      progress: 0,
      completedPlayers: [],
    }),

  setStage: (index) => {
    const stages = get().stages;
    let progress = 0;
    for (let i = 0; i < index; i++) {
      progress += stages[i].weight;
    }
    set({ currentStageIndex: index, progress });
  },

  addCompletedPlayer: (playerName) =>
    set((state) => ({
      completedPlayers: [...state.completedPlayers, playerName],
    })),

  setProgress: (progress) => set({ progress: Math.min(progress, 100) }),

  finishLoading: () =>
    set({
      isActive: false,
      progress: 100,
      currentStageIndex: STAGES.length,
    }),

  resetLoading: () =>
    set({
      isActive: false,
      currentStageIndex: 0,
      progress: 0,
      completedPlayers: [],
    }),
}));
