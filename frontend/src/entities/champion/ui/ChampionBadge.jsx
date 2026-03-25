import { ChampionIcon } from './ChampionIcon';
import { formatWinRate } from '../../../shared/lib/formatWinRate';
import { cn } from '../../../shared/lib/cn';

export function ChampionBadge({
  championName,
  championNameKo,
  championId,
  winRate,
  kda,
  games,
  className,
  size = 'md',
}) {
  const sizes = {
    sm: { icon: 28, text: 'text-[10px]' },
    md: { icon: 36, text: 'text-xs' },
    lg: { icon: 44, text: 'text-sm' },
  };

  const s = sizes[size] || sizes.md;

  return (
    <div
      className={cn(
        'flex items-center gap-2 bg-gray-800 rounded-lg px-2.5 py-1.5',
        'border border-gray-700 hover:border-gray-600 transition-colors',
        className
      )}
    >
      <ChampionIcon
        championName={championName}
        championNameKo={championNameKo}
        championId={championId}
        size={s.icon}
        showTooltip={false}
      />
      <div className={cn('flex flex-col', s.text)}>
        <span className="text-gray-200 font-semibold leading-tight">
          {championNameKo || championName}
        </span>
        <div className="flex items-center gap-1.5 text-gray-400">
          {winRate != null && (
            <span
              className={cn(
                'font-medium',
                winRate >= 0.6
                  ? 'text-emerald-400'
                  : winRate >= 0.5
                    ? 'text-amber-400'
                    : 'text-red-400'
              )}
            >
              {formatWinRate(winRate)}
            </span>
          )}
          {kda != null && (
            <span className="text-gray-500">KDA {kda.toFixed(1)}</span>
          )}
          {games != null && (
            <span className="text-gray-500">{games}판</span>
          )}
        </div>
      </div>
    </div>
  );
}
