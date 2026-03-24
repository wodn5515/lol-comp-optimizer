import { PlayerCard } from '../../../entities/player';
import { usePlayerSummary } from '../model/usePlayerSummary';

export function PlayerSummary() {
  const { players, hasPlayers } = usePlayerSummary();

  if (!hasPlayers) return null;

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-lg font-bold text-gray-100">플레이어 정보</h2>
        <span className="text-xs text-gray-500 bg-slate-800/60 px-2 py-0.5 rounded-full">
          {players.length}명
        </span>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-3 scrollbar-thin">
        {players.map((player, index) => (
          <div key={`${player.game_name}-${player.tag_line}-${index}`} className="flex-shrink-0">
            <PlayerCard player={player} compact />
          </div>
        ))}
      </div>
    </div>
  );
}
