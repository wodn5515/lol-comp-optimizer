import { ProgressBar } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { useAnalyzeStore } from '../../../features/analyze-comp';

export function LoadingProgress() {
  const { isLoading, stage } = useAnalyzeStore();

  if (!isLoading) return null;

  const stages = [
    { label: '플레이어 정보 조회 중...', key: 'fetch' },
    { label: '전적 분석 중...', key: 'analyze' },
    { label: '조합 최적화 중...', key: 'optimize' },
  ];

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="relative rounded-xl border border-slate-700/50 bg-gradient-to-b from-slate-900/95 to-slate-950/95 p-8 shadow-xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500/10 mb-4">
            <svg
              className="animate-spin h-8 w-8 text-amber-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-gray-100 mb-1">분석 진행 중</h3>
          <p className="text-sm text-gray-400">
            Riot API에서 데이터를 수집하고 있습니다
          </p>
        </div>

        <div className="space-y-3 mb-6">
          {stages.map((s, index) => {
            const isActive = stage.includes(s.label.replace('...', '').trim()) ||
                            (index === 0 && isLoading && !stage);
            const isComplete = false;

            return (
              <div
                key={s.key}
                className={cn(
                  'flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-300',
                  isActive
                    ? 'bg-amber-500/10 border border-amber-500/20'
                    : 'bg-slate-800/20 border border-transparent'
                )}
              >
                <div
                  className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                    isActive
                      ? 'bg-amber-500/20 text-amber-400 animate-pulse'
                      : isComplete
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-slate-700/30 text-gray-600'
                  )}
                >
                  {isComplete ? '\u2713' : index + 1}
                </div>
                <span
                  className={cn(
                    'text-sm font-medium',
                    isActive
                      ? 'text-amber-300'
                      : isComplete
                        ? 'text-emerald-400'
                        : 'text-gray-600'
                  )}
                >
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>

        <ProgressBar
          value={33}
          max={100}
          showPercent={false}
          barColor="bg-gradient-to-r from-amber-600 to-amber-400"
        />

        <p className="text-[11px] text-gray-500 text-center mt-4">
          Rate Limit으로 인해 최대 2분 정도 소요될 수 있습니다
        </p>
      </div>
    </div>
  );
}
