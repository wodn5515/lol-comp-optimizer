import { useMemo } from 'react';
import { useBanPickStore } from '../../../features/analyze-comp';

export function useResultData() {
  const storeRecommendations = useBanPickStore((s) => s.recommendations);

  const recommendations = useMemo(() => {
    if (!storeRecommendations || storeRecommendations.length === 0) return [];
    return [...storeRecommendations].sort((a, b) => a.rank - b.rank);
  }, [storeRecommendations]);

  const hasResults = recommendations.length > 0;

  return {
    recommendations,
    hasResults,
  };
}
