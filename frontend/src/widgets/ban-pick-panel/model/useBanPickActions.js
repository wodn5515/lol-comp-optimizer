import { useEffect, useRef, useCallback } from 'react';
import { useBanPickStore } from '../../../features/analyze-comp';
import { optimizeComp } from '../../../features/analyze-comp/api/analyzeComp';

/**
 * 밴/픽 변경 시 자동으로 최적화 API를 호출하는 훅
 * 500ms 디바운스 적용
 */
export function useBanPickActions() {
  const analyzedPlayers = useBanPickStore((s) => s.analyzedPlayers);
  const bannedChampions = useBanPickStore((s) => s.bannedChampions);
  const enemyPicks = useBanPickStore((s) => s.enemyPicks);
  const lockedPicks = useBanPickStore((s) => s.lockedPicks);
  const setRecommendations = useBanPickStore((s) => s.setRecommendations);
  const setIsOptimizing = useBanPickStore((s) => s.setIsOptimizing);

  const timerRef = useRef(null);
  const abortRef = useRef(null);

  const fetchOptimization = useCallback(async () => {
    if (!analyzedPlayers || analyzedPlayers.length === 0) return;

    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setIsOptimizing(true);

    try {
      const result = await optimizeComp({
        players: analyzedPlayers,
        bannedChampions,
        enemyPicks,
        lockedPicks,
      });

      if (result?.recommendations) {
        setRecommendations(
          result.recommendations.sort((a, b) => a.rank - b.rank)
        );
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('최적화 실패:', err);
      }
    } finally {
      setIsOptimizing(false);
    }
  }, [analyzedPlayers, bannedChampions, enemyPicks, lockedPicks, setRecommendations, setIsOptimizing]);

  useEffect(() => {
    if (!analyzedPlayers || analyzedPlayers.length === 0) return;

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      fetchOptimization();
    }, 500);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [bannedChampions, enemyPicks, lockedPicks, fetchOptimization]);

  // Initial fetch when players are first set
  const hasInitialFetch = useRef(false);
  useEffect(() => {
    if (analyzedPlayers.length > 0 && !hasInitialFetch.current) {
      hasInitialFetch.current = true;
      fetchOptimization();
    }
  }, [analyzedPlayers, fetchOptimization]);

  return { fetchOptimization };
}
