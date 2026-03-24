import { create } from 'zustand';
import { analyzeComp, analyzePlayers } from '../api/analyzeComp';

export const useAnalyzeStore = create((set, get) => ({
  result: null,
  isLoading: false,
  error: null,
  stage: '',

  analyze: async ({ apiKey, players, matchCount }) => {
    set({ isLoading: true, error: null, result: null, stage: '분석 요청 중...' });

    try {
      set({ stage: '플레이어 정보 조회 중...' });
      const data = await analyzeComp({ apiKey, players, matchCount });

      set({
        result: data,
        isLoading: false,
        stage: '완료',
        error: null,
      });

      return data;
    } catch (err) {
      set({
        error: err.message || '분석 중 오류가 발생했습니다.',
        isLoading: false,
        stage: '',
      });
      throw err;
    }
  },

  analyzePlayers: async ({ apiKey, players, matchCount }) => {
    set({ isLoading: true, error: null, result: null, stage: '분석 요청 중...' });

    try {
      set({ stage: '플레이어 정보 조회 중...' });
      const data = await analyzePlayers({ apiKey, players, matchCount });

      set({
        result: data,
        isLoading: false,
        stage: '완료',
        error: null,
      });

      return data;
    } catch (err) {
      set({
        error: err.message || '분석 중 오류가 발생했습니다.',
        isLoading: false,
        stage: '',
      });
      throw err;
    }
  },

  clearResult: () => set({ result: null, error: null, stage: '' }),
  clearError: () => set({ error: null }),
}));
