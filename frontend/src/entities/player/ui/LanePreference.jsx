import { LANE_LABELS } from '../../../shared/config/constants';
import { cn } from '../../../shared/lib/cn';

const LANE_ORDER = ['TOP', 'JG', 'MID', 'ADC', 'SUP'];

export function LanePreference({ laneStats, compact = false }) {
  if (!laneStats || Object.keys(laneStats).length === 0) return null;

  const totalGames = LANE_ORDER.reduce(
    (sum, lane) => sum + (laneStats[lane]?.games || 0),
    0
  );

  if (totalGames === 0) return null;

  const data = LANE_ORDER.map((lane) => ({
    lane,
    label: LANE_LABELS[lane] || lane,
    games: laneStats[lane]?.games || 0,
    percent: totalGames > 0 ? ((laneStats[lane]?.games || 0) / totalGames) * 100 : 0,
    winRate: laneStats[lane]?.win_rate || 0,
  }));

  const maxPercent = Math.max(...data.map((d) => d.percent), 1);

  return (
    <div className={cn('flex flex-col gap-1', compact && 'gap-0.5')}>
      {data.map((item) => (
        <div key={item.lane} className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 w-6 text-right font-medium">
            {item.label}
          </span>
          <div className="flex-1 h-3 bg-slate-800/60 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(item.percent / maxPercent) * 100}%`,
                background:
                  item.percent > 0
                    ? `linear-gradient(to right, #0397ab, #0397ab${item.winRate > 0.5 ? 'cc' : '88'})`
                    : 'transparent',
              }}
            />
          </div>
          <span className="text-[10px] text-gray-500 w-6 font-mono">
            {item.games > 0 ? item.games : '-'}
          </span>
        </div>
      ))}
    </div>
  );
}
