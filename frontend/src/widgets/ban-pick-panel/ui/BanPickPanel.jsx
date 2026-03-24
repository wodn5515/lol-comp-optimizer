import { useState, useRef, useEffect, useMemo } from 'react';
import { Card, CardContent } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { CHAMPION_ICON_URL } from '../../../shared/config/constants';
import { useBanPickStore } from '../../../features/analyze-comp';
import { ChampionIcon } from '../../../entities/champion';

function ChampionSearchInput({ onSelect, placeholder, excludeList = [] }) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  const analyzedPlayers = useBanPickStore((s) => s.analyzedPlayers);

  const allChampions = useMemo(() => {
    const champSet = new Set();
    if (analyzedPlayers) {
      analyzedPlayers.forEach((player) => {
        if (player.top_champions) {
          player.top_champions.forEach((c) => {
            champSet.add(c.champion_name);
          });
        }
      });
    }
    return Array.from(champSet).sort();
  }, [analyzedPlayers]);

  const filtered = useMemo(() => {
    if (!query.trim()) return allChampions.filter((c) => !excludeList.includes(c));
    const q = query.toLowerCase();
    return allChampions
      .filter((c) => !excludeList.includes(c))
      .filter((c) => c.toLowerCase().includes(q));
  }, [query, allChampions, excludeList]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target) &&
        inputRef.current &&
        !inputRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (championName) => {
    onSelect(championName);
    setQuery('');
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
        className={cn(
          'w-full rounded-lg border bg-gray-900 px-3 py-2 text-sm text-gray-100',
          'placeholder:text-gray-600',
          'border-gray-700 focus:ring-2 focus:ring-amber-500/40 focus:outline-none',
          'transition-colors'
        )}
      />
      {isOpen && filtered.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
        >
          {filtered.map((champ) => (
            <button
              key={champ}
              type="button"
              onClick={() => handleSelect(champ)}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 transition-colors text-left"
            >
              <ChampionIcon championName={champ} size={20} showTooltip={false} />
              <span>{champ}</span>
            </button>
          ))}
        </div>
      )}
      {isOpen && query.trim() && filtered.length === 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-gray-700 bg-gray-900 p-3">
          <p className="text-xs text-gray-500 text-center">챔피언을 찾을 수 없습니다</p>
        </div>
      )}
    </div>
  );
}

function BanSection() {
  const bannedChampions = useBanPickStore((s) => s.bannedChampions);
  const addBan = useBanPickStore((s) => s.addBan);
  const removeBan = useBanPickStore((s) => s.removeBan);
  const enemyPicks = useBanPickStore((s) => s.enemyPicks);
  const lockedPicks = useBanPickStore((s) => s.lockedPicks);

  const excludeList = [
    ...bannedChampions,
    ...enemyPicks,
    ...Object.values(lockedPicks),
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-red-400">
          밴 목록
        </h3>
        <span className="text-xs text-gray-500">
          {bannedChampions.length} / 10
        </span>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: 10 }).map((_, i) => {
          const champ = bannedChampions[i];
          return (
            <div
              key={i}
              className={cn(
                'relative aspect-square rounded-lg flex items-center justify-center',
                'border transition-colors',
                champ
                  ? 'bg-red-950 border-red-800'
                  : 'bg-gray-800/50 border-gray-700'
              )}
            >
              {champ ? (
                <>
                  <ChampionIcon
                    championName={champ}
                    size={36}
                    showTooltip={false}
                    className="opacity-60"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="w-6 h-6 text-red-500/80"
                    >
                      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeBan(champ)}
                    className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-600 text-white flex items-center justify-center text-[10px] hover:bg-red-500 transition-colors z-10"
                    title={`${champ} 밴 해제`}
                  >
                    x
                  </button>
                </>
              ) : (
                <span className="text-gray-600 text-xs">{i + 1}</span>
              )}
            </div>
          );
        })}
      </div>

      {bannedChampions.length < 10 && (
        <ChampionSearchInput
          onSelect={addBan}
          placeholder="밴할 챔피언 검색..."
          excludeList={excludeList}
        />
      )}
    </div>
  );
}

function EnemyPickSection() {
  const enemyPicks = useBanPickStore((s) => s.enemyPicks);
  const addEnemyPick = useBanPickStore((s) => s.addEnemyPick);
  const removeEnemyPick = useBanPickStore((s) => s.removeEnemyPick);
  const bannedChampions = useBanPickStore((s) => s.bannedChampions);
  const lockedPicks = useBanPickStore((s) => s.lockedPicks);

  const excludeList = [
    ...bannedChampions,
    ...enemyPicks,
    ...Object.values(lockedPicks),
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-red-400">
          적 팀 픽
        </h3>
        <span className="text-xs text-gray-500">
          {enemyPicks.length} / 5
        </span>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: 5 }).map((_, i) => {
          const champ = enemyPicks[i];
          return (
            <div
              key={i}
              className={cn(
                'relative aspect-square rounded-lg flex flex-col items-center justify-center gap-1',
                'border-2 transition-colors',
                champ
                  ? 'bg-red-950 border-red-800'
                  : 'bg-gray-800/50 border-gray-700 border-dashed'
              )}
            >
              {champ ? (
                <>
                  <ChampionIcon
                    championName={champ}
                    size={32}
                    showTooltip={false}
                  />
                  <span className="text-[9px] text-gray-400 truncate max-w-full px-1">
                    {champ}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeEnemyPick(champ)}
                    className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-600 text-white flex items-center justify-center text-[10px] hover:bg-red-500 transition-colors z-10"
                    title={`${champ} 제거`}
                  >
                    x
                  </button>
                </>
              ) : (
                <span className="text-gray-600 text-xs">{i + 1}</span>
              )}
            </div>
          );
        })}
      </div>

      {enemyPicks.length < 5 && (
        <ChampionSearchInput
          onSelect={addEnemyPick}
          placeholder="적 팀 챔피언 검색..."
          excludeList={excludeList}
        />
      )}
    </div>
  );
}

function AllyLockSection() {
  const analyzedPlayers = useBanPickStore((s) => s.analyzedPlayers);
  const lockedPicks = useBanPickStore((s) => s.lockedPicks);
  const lockPick = useBanPickStore((s) => s.lockPick);
  const unlockPick = useBanPickStore((s) => s.unlockPick);
  const bannedChampions = useBanPickStore((s) => s.bannedChampions);
  const enemyPicks = useBanPickStore((s) => s.enemyPicks);

  const unavailable = [
    ...bannedChampions,
    ...enemyPicks,
    ...Object.values(lockedPicks),
  ];

  if (!analyzedPlayers || analyzedPlayers.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-amber-400">
        아군 픽 고정
      </h3>

      <div className="space-y-2">
        {analyzedPlayers.map((player) => {
          const playerKey = `${player.game_name}#${player.tag_line}`;
          const isLocked = !!lockedPicks[playerKey];
          const lockedChamp = lockedPicks[playerKey];

          const playerChampions = (player.top_champions || [])
            .map((c) => c.champion_name)
            .filter((c) => !unavailable.includes(c) || c === lockedChamp);

          return (
            <div
              key={playerKey}
              className={cn(
                'flex items-center gap-3 p-2.5 rounded-lg transition-colors',
                'border',
                isLocked
                  ? 'bg-amber-950 border-amber-800'
                  : 'bg-gray-800/50 border-gray-700'
              )}
            >
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-200 truncate">
                  {player.game_name}
                  <span className="text-gray-500">#{player.tag_line}</span>
                </p>
              </div>

              {isLocked ? (
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 bg-amber-900 rounded-md px-2 py-1">
                    <ChampionIcon
                      championName={lockedChamp}
                      size={20}
                      showTooltip={false}
                    />
                    <span className="text-xs text-amber-300 font-medium">
                      {lockedChamp}
                    </span>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="w-3.5 h-3.5 text-amber-400"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <button
                    type="button"
                    onClick={() => unlockPick(playerKey)}
                    className="text-gray-500 hover:text-amber-400 transition-colors p-1"
                    title="고정 해제"
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
              ) : (
                <select
                  value=""
                  onChange={(e) => {
                    if (e.target.value) {
                      lockPick(playerKey, e.target.value);
                    }
                  }}
                  className={cn(
                    'rounded-md border bg-gray-900 px-2 py-1.5 text-xs text-gray-300',
                    'border-gray-700 focus:ring-1 focus:ring-amber-500/40 focus:outline-none',
                    'cursor-pointer max-w-[140px]'
                  )}
                >
                  <option value="">챔피언 선택...</option>
                  {playerChampions.map((champ) => (
                    <option key={champ} value={champ}>
                      {champ}
                    </option>
                  ))}
                </select>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function BanPickPanel() {
  return (
    <Card>
      <CardContent className="p-5 space-y-6">
        <div className="text-center mb-2">
          <h2 className="text-base font-bold text-gray-100">
            밴/픽 설정
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            밴과 적 팀 픽을 설정하면 추천이 자동으로 업데이트됩니다
          </p>
        </div>

        <BanSection />

        <div className="border-t border-gray-800" />

        <EnemyPickSection />

        <div className="border-t border-gray-800" />

        <AllyLockSection />
      </CardContent>
    </Card>
  );
}
