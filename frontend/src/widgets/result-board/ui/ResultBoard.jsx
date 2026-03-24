import { TeamCompCard } from '../../../entities/composition';
import { useResultData } from '../model/useResultData';

export function ResultBoard() {
  const { recommendations, hasResults } = useResultData();

  if (!hasResults) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-sm">추천 조합이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 mb-2">
        <h2 className="text-lg font-bold text-gray-100">추천 조합</h2>
        <span className="text-xs text-gray-500 bg-slate-800/60 px-2 py-0.5 rounded-full">
          상위 {recommendations.length}개
        </span>
      </div>

      <div className="grid gap-5">
        {recommendations.map((rec) => (
          <TeamCompCard key={rec.rank} recommendation={rec} />
        ))}
      </div>
    </div>
  );
}
