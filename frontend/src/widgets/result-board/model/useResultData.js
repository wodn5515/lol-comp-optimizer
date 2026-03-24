import { useMemo } from 'react';
import { useAnalyzeStore } from '../../../features/analyze-comp';

export function useResultData() {
  const result = useAnalyzeStore((s) => s.result);

  const recommendations = useMemo(() => {
    if (!result?.recommendations) return [];
    return result.recommendations.sort((a, b) => a.rank - b.rank);
  }, [result]);

  const hasResults = recommendations.length > 0;

  return {
    recommendations,
    hasResults,
  };
}
