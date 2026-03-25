import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { MATCH_COUNT_OPTIONS } from '../../../shared/config/constants';
import { getRecentSummoners, addRecentSummoners } from '../../../shared/lib/recentSummoners';
import { ApiKeyInput, useApiKeyStore } from '../../../features/setup-api-key';
import { AddPlayerButton, usePlayerListStore } from '../../../features/add-player';
import { AnalyzeButton, useAnalyzeStore, useBanPickStore } from '../../../features/analyze-comp';
import { usePlayerStore } from '../../../entities/player';
import { usePlayerFormStore } from '../model/usePlayerForm';

function SummonerInput({ value, onChange, onEnter, error, index }) {
  const [showRecent, setShowRecent] = useState(false);
  const wrapperRef = useRef(null);

  // 다른 칸에 이미 입력된 소환사 제외를 위해 부모에서 전달받지 않고
  // playerInputs를 직접 참조
  const playerInputs = usePlayerListStore((s) => s.playerInputs);
  const usedSummoners = playerInputs
    .filter((p) => p.rawInput && p.rawInput.includes('#'))
    .map((p) => p.rawInput.trim().toLowerCase());

  const recentList = getRecentSummoners().filter(
    (s) => !usedSummoners.includes(s.toLowerCase())
  );

  // 바깥 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowRecent(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={wrapperRef}>
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 font-medium z-10">
        {index + 1}.
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowRecent(false);
        }}
        onFocus={() => {
          if (!value && recentList.length > 0) setShowRecent(true);
        }}
        onClick={() => {
          if (!value && recentList.length > 0) setShowRecent(true);
        }}
        placeholder="소환사이름#태그 (예: Hide on bush#KR1)"
        className={cn(
          'w-full rounded-lg border bg-gray-900 pl-8 pr-4 py-2.5 text-sm text-gray-100',
          'placeholder:text-gray-600',
          'transition-colors',
          'focus:outline-none',
          error
            ? 'border-red-600'
            : 'border-gray-700 focus:border-amber-500 hover:border-gray-600'
        )}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onEnter();
          if (e.key === 'Escape') setShowRecent(false);
        }}
      />
      {showRecent && recentList.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
          <p className="px-3 py-1.5 text-[10px] text-gray-500 border-b border-gray-700">최근 검색</p>
          {recentList.map((summoner) => (
            <button
              key={summoner}
              type="button"
              className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-700 transition-colors cursor-pointer"
              onMouseDown={(e) => {
                e.preventDefault();
                onChange(summoner);
                setShowRecent(false);
              }}
            >
              {summoner}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function PlayerInputForm() {
  const navigate = useNavigate();
  const [multiMode, setMultiMode] = useState(false);
  const [multiText, setMultiText] = useState('');
  const { apiKey, isValid: isApiKeyValid } = useApiKeyStore();
  const {
    playerInputs,
    removePlayerInput,
    updatePlayerInput,
    getValidPlayers,
    fillFromMultiSearch,
  } = usePlayerListStore();
  const { matchCount, setMatchCount, errors, setError, clearError, clearAllErrors, validateRiotId } =
    usePlayerFormStore();
  const { analyzePlayers: analyzePlayersAction, isLoading } = useAnalyzeStore();
  const { setPlayers } = usePlayerStore();
  const { setAnalyzedPlayers, reset: resetBanPick } = useBanPickStore();

  const handleRiotIdChange = (id, value) => {
    updatePlayerInput(id, value);
    const error = validateRiotId(value);
    if (error) {
      setError(id, error);
    } else {
      clearError(id);
    }
  };

  const handleMultiTextChange = (text) => {
    setMultiText(text);
    if (text.trim()) {
      fillFromMultiSearch(text);
      clearAllErrors();
    }
  };

  const handleAnalyze = async () => {
    clearAllErrors();

    if (!isApiKeyValid) {
      return;
    }

    let hasError = false;
    playerInputs.forEach((input) => {
      const error = validateRiotId(input.rawInput);
      if (error) {
        setError(input.id, error);
        hasError = true;
      }
    });

    const validPlayers = getValidPlayers();
    if (validPlayers.length < 2) {
      setError('global', '최소 2명의 소환사를 입력해주세요');
      hasError = true;
    }

    if (hasError) return;

    try {
      const result = await analyzePlayersAction({
        apiKey,
        players: validPlayers.map((p) => ({
          game_name: p.gameName,
          tag_line: p.tagLine,
        })),
        matchCount,
      });

      if (result) {
        // 최근 소환사 저장
        addRecentSummoners(
          validPlayers.map((p) => `${p.gameName}#${p.tagLine}`)
        );
        resetBanPick();
        setPlayers(result.players || []);
        setAnalyzedPlayers(result.players || []);
        navigate('/banpick');
      }
    } catch {
      // error is handled by the store
    }
  };

  const canRemove = playerInputs.length > 2;

  return (
    <div className="w-full max-w-lg mx-auto space-y-5">
      <Card>
        <CardContent className="p-5">
          <ApiKeyInput />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-gray-200">
              소환사 입력
            </h3>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setMultiMode(!multiMode)}
                className={cn(
                  'text-[11px] px-2.5 py-1 rounded-full border transition-all cursor-pointer',
                  multiMode
                    ? 'bg-sky-950 border-sky-800 text-sky-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-300'
                )}
              >
                멀티서치
              </button>
              <span className="text-xs text-gray-500">
                2~5명
              </span>
            </div>
          </div>

          {multiMode && (
            <div className="space-y-2">
              <textarea
                value={multiText}
                onChange={(e) => handleMultiTextChange(e.target.value)}
                placeholder={
                  '롤 로비 채팅을 붙여넣거나 쉼표로 구분하여 입력하세요\n\n' +
                  '예시 1) 채팅 복붙:\n' +
                  '미 키 #0313 님이 로비에 참가하셨습니다.\n' +
                  'dlwldms #iuiu 님이 로비에 참가하셨습니다.\n\n' +
                  '예시 2) 쉼표 구분:\n' +
                  '미 키 #0313,dlwldms #iuiu,Daemi #Arneb'
                }
                rows={5}
                className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2.5 text-sm text-gray-100 placeholder:text-gray-600 placeholder:text-[11px] focus:outline-none focus:border-amber-500 resize-none leading-relaxed"
              />
              {playerInputs.some((p) => p.rawInput) && (
                <p className="text-[11px] text-sky-400">
                  {playerInputs.filter((p) => p.rawInput).length}명 인식됨 — 아래 개별 입력에 반영됨
                </p>
              )}
            </div>
          )}

          {playerInputs.map((input, index) => (
            <div key={input.id} className="flex gap-2 items-start">
              <div className="flex-1">
                <SummonerInput
                  value={input.rawInput}
                  onChange={(v) => handleRiotIdChange(input.id, v)}
                  onEnter={handleAnalyze}
                  error={errors[input.id]}
                  index={index}
                />
                {errors[input.id] && (
                  <p className="text-[11px] text-red-400 mt-1">
                    {errors[input.id]}
                  </p>
                )}
              </div>
              {canRemove && (
                <button
                  type="button"
                  onClick={() => removePlayerInput(input.id)}
                  className="mt-2 text-gray-500 hover:text-red-400 transition-colors p-1"
                  title="제거"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="w-4 h-4"
                  >
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}
            </div>
          ))}

          {!multiMode && <AddPlayerButton />}

          {errors.global && (
            <p className="text-xs text-red-400 text-center">
              {errors.global}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">
              분석 매치 수
            </h3>
            <span className="text-xs text-gray-500">
              최근 전적
            </span>
          </div>

          <div className="flex gap-2 mb-5">
            {MATCH_COUNT_OPTIONS.map((count) => (
              <button
                key={count}
                onClick={() => setMatchCount(count)}
                className={cn(
                  'flex-1 py-2 rounded-lg text-sm font-semibold transition-colors',
                  'border cursor-pointer',
                  matchCount === count
                    ? 'bg-amber-950 border-amber-700 text-amber-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300'
                )}
              >
                {count}판
              </button>
            ))}
          </div>

          <AnalyzeButton
            onClick={handleAnalyze}
            disabled={!isApiKeyValid || isLoading}
            loading={isLoading}
          />

          {!isApiKeyValid && apiKey && (
            <p className="text-[11px] text-amber-400 text-center mt-2">
              유효한 API 키를 먼저 설정해주세요
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
