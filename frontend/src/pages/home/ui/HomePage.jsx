import { PlayerInputForm } from '../../../widgets/player-input-form';
import { LoadingProgress } from '../../../widgets/loading-progress';
import { useAnalyzeStore } from '../../../features/analyze-comp';

export function HomePage() {
  const isLoading = useAnalyzeStore((s) => s.isLoading);
  const error = useAnalyzeStore((s) => s.error);
  const clearError = useAnalyzeStore((s) => s.clearError);

  return (
    <div className="min-h-screen bg-gray-950">
      <div>
        <div className="max-w-2xl mx-auto px-4 py-12">
          <header className="text-center mb-10">
            <p className="text-xs font-medium text-amber-500 mb-3 uppercase tracking-wider">
              LoL Comp Optimizer
            </p>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-100 mb-3">
              최적 조합을 찾아보세요
            </h1>
            <p className="text-gray-400 text-sm md:text-base max-w-md mx-auto leading-relaxed">
              소환사명을 입력하면 전적과 챔피언풀을 분석하여
              <br className="hidden md:block" />
              최적의 라인 배정과 챔피언 조합을 추천합니다
            </p>
          </header>

          {error && (
            <div className="mb-5 p-4 rounded-lg bg-red-950 border border-red-900 flex items-start gap-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-red-300 font-medium">오류 발생</p>
                <p className="text-xs text-red-400 mt-0.5">{error}</p>
              </div>
              <button
                onClick={clearError}
                className="text-red-400 hover:text-red-300 transition-colors"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4"
                >
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>
          )}

          {isLoading ? <LoadingProgress /> : <PlayerInputForm />}
        </div>
      </div>
    </div>
  );
}
