import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Button } from '../../../shared/ui';
import { PlayerSummary } from '../../../widgets/player-summary';
import { ResultBoard } from '../../../widgets/result-board';
import { useAnalyzeStore, useBanPickStore } from '../../../features/analyze-comp';

export function ResultPage() {
  const navigate = useNavigate();
  const clearResult = useAnalyzeStore((s) => s.clearResult);
  const analyzedPlayers = useBanPickStore((s) => s.analyzedPlayers);
  const recommendations = useBanPickStore((s) => s.recommendations);

  useEffect(() => {
    if (!analyzedPlayers || analyzedPlayers.length === 0) {
      navigate('/');
    }
  }, [analyzedPlayers, navigate]);

  if (!analyzedPlayers || analyzedPlayers.length === 0) return null;

  const handleGoBack = () => {
    clearResult();
    navigate('/');
  };

  const handleGoToBanPick = () => {
    if (analyzedPlayers && analyzedPlayers.length > 0) {
      navigate('/banpick');
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <div>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <header className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-100">
                분석 결과
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                최적의 라인 배정과 챔피언 조합을 확인하세요
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="md" onClick={handleGoToBanPick}>
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
                밴픽으로 돌아가기
              </Button>
              <Button variant="secondary" size="md" onClick={handleGoBack}>
                다시 분석하기
              </Button>
            </div>
          </header>

          <PlayerSummary />
          <ResultBoard />

          <footer className="mt-12 pb-8 text-center">
            <Button
              variant="primary"
              size="lg"
              onClick={handleGoBack}
            >
              새로운 조합 분석하기
            </Button>
          </footer>
        </div>
      </div>
    </div>
  );
}
