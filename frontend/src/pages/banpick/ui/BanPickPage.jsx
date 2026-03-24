import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Button } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { useAnalyzeStore, useBanPickStore } from '../../../features/analyze-comp';
import { PlayerSummary } from '../../../widgets/player-summary';
import { BanPickPanel, useBanPickActions } from '../../../widgets/ban-pick-panel';
import { TeamCompCard } from '../../../entities/composition';

function RecommendationsPanel() {
  const recommendations = useBanPickStore((s) => s.recommendations);
  const isOptimizing = useBanPickStore((s) => s.isOptimizing);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-base font-bold text-gray-100">
          추천 조합
        </h2>
        {isOptimizing && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800">
            <svg
              className="animate-spin h-3 w-3 text-amber-400"
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
            <span className="text-[11px] text-amber-400 font-medium">
              최적화 중...
            </span>
          </div>
        )}
      </div>

      {recommendations.length === 0 && !isOptimizing && (
        <div className="text-center py-12 rounded-lg border border-gray-800 bg-gray-900">
          <p className="text-gray-500 text-sm">
            밴/픽을 설정하면 추천 조합이 표시됩니다
          </p>
        </div>
      )}

      <div className={cn('grid gap-4 transition-opacity duration-300', isOptimizing && 'opacity-60')}>
        {recommendations.map((rec) => (
          <TeamCompCard key={rec.rank} recommendation={rec} />
        ))}
      </div>
    </div>
  );
}

export function BanPickPage() {
  const navigate = useNavigate();
  const analyzedPlayers = useBanPickStore((s) => s.analyzedPlayers);
  const clearResult = useAnalyzeStore((s) => s.clearResult);
  const resetBanPick = useBanPickStore((s) => s.reset);

  // Trigger optimization on ban/pick changes
  useBanPickActions();

  useEffect(() => {
    if (!analyzedPlayers || analyzedPlayers.length === 0) {
      navigate('/');
    }
  }, [analyzedPlayers, navigate]);

  if (!analyzedPlayers || analyzedPlayers.length === 0) return null;

  const handleGoHome = () => {
    clearResult();
    resetBanPick();
    navigate('/');
  };

  const handleReanalyze = () => {
    resetBanPick();
    clearResult();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <div>
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <header className="flex items-center justify-between mb-6">
            <button
              type="button"
              onClick={handleGoHome}
              className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4"
              >
                <path
                  fillRule="evenodd"
                  d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
                  clipRule="evenodd"
                />
              </svg>
              돌아가기
            </button>

            <div className="text-center">
              <h1 className="text-xl font-bold text-gray-100">
                밴/픽 단계
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                밴과 픽을 설정하여 최적 조합을 확인하세요
              </p>
            </div>

            <Button variant="secondary" size="md" onClick={handleReanalyze}>
              다시 분석
            </Button>
          </header>

          {/* Player Summary */}
          <PlayerSummary />

          {/* Main Content: Ban/Pick + Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Ban/Pick Panel */}
            <div>
              <BanPickPanel />
            </div>

            {/* Right: Recommendations */}
            <div>
              <RecommendationsPanel />
            </div>
          </div>

          {/* Footer */}
          <footer className="mt-8 pb-8 text-center">
            <Button
              variant="secondary"
              size="md"
              onClick={() => navigate('/result')}
            >
              상세 결과 보기
            </Button>
          </footer>
        </div>
      </div>
    </div>
  );
}
