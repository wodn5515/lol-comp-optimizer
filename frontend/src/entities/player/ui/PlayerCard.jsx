import { Card, CardContent } from '../../../shared/ui';
import { PROFILE_ICON_URL, TIER_COLORS, LANE_LABELS } from '../../../shared/config/constants';
import { formatTier } from '../../../shared/lib/tierToScore';
import { formatWinRate } from '../../../shared/lib/formatWinRate';
import { cn } from '../../../shared/lib/cn';
import { ChampionIcon } from '../../champion';
import { LanePreference } from './LanePreference';

export function PlayerCard({ player, compact = false }) {
  const {
    game_name,
    tag_line,
    tier,
    rank,
    lp,
    profile_icon_id,
    lane_stats,
    top_champions,
  } = player;

  const tierColor = TIER_COLORS[tier?.toUpperCase()] || '#6b6b6b';

  return (
    <Card
      className={cn(
        'overflow-hidden',
        compact ? 'min-w-[240px] max-w-[280px]' : 'w-full'
      )}
    >
      <div
        className="h-1 w-full"
        style={{ background: tierColor }}
      />
      <CardContent className={compact ? 'p-3' : 'p-4'}>
        <div className="flex items-center gap-3 mb-3">
          <div className="relative">
            <img
              src={PROFILE_ICON_URL(profile_icon_id || 29)}
              alt={game_name}
              className="w-12 h-12 rounded-lg border-2 object-cover"
              style={{ borderColor: tierColor }}
              onError={(e) => {
                e.target.src = PROFILE_ICON_URL(29);
              }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-gray-100 truncate text-sm">
              {game_name}
              <span className="text-gray-500 font-normal">#{tag_line}</span>
            </p>
            <p
              className="text-xs font-semibold mt-0.5"
              style={{ color: tierColor }}
            >
              {formatTier(tier, rank, lp)}
            </p>
          </div>
        </div>

        {top_champions && top_champions.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1.5 font-medium">모스트 챔피언</p>
            <div className="flex gap-2">
              {top_champions.slice(0, 3).map((champ) => (
                <div
                  key={champ.champion_id}
                  className="flex items-center gap-1.5 bg-gray-800 rounded-lg px-2 py-1"
                >
                  <ChampionIcon
                    championName={champ.champion_name}
                    championNameKo={champ.champion_name_ko}
                    size={24}
                  />
                  <div className="text-xs">
                    <p className="text-gray-300 font-medium leading-tight">
                      {formatWinRate(champ.win_rate)}
                    </p>
                    <p className="text-gray-500 leading-tight">
                      {champ.games}판
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {lane_stats && Object.keys(lane_stats).length > 0 && (
          <div>
            <p className="text-xs text-gray-500 mb-1.5 font-medium">라인 선호도</p>
            <LanePreference laneStats={lane_stats} compact={compact} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
