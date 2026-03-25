import { Card, CardContent } from '../../../shared/ui';
import { LANE_LABELS } from '../../../shared/config/constants';
import { formatWinRate } from '../../../shared/lib/formatWinRate';
import { cn } from '../../../shared/lib/cn';
import { ChampionIcon } from '../../champion';
import { TeamAnalysisChart } from './TeamAnalysisChart';

const RANK_STYLES = {
  1: {
    badge: 'bg-amber-500 text-gray-900',
    border: 'border-amber-500/40',
  },
  2: {
    badge: 'bg-gray-400 text-gray-900',
    border: 'border-gray-500/40',
  },
  3: {
    badge: 'bg-amber-700 text-gray-100',
    border: 'border-amber-700/40',
  },
};

const LANE_ORDER = ['TOP', 'JG', 'MID', 'ADC', 'SUP'];

export function TeamCompCard({ recommendation }) {
  const { rank, total_score, assignments, team_analysis } = recommendation;

  const style = RANK_STYLES[rank] || RANK_STYLES[3];

  const assignmentByLane = {};
  assignments.forEach((a) => {
    assignmentByLane[a.lane] = a;
  });

  return (
    <Card className={cn('overflow-hidden', style.border)}>
      <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-lg',
              style.badge
            )}
          >
            {rank}
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-100">
              추천 조합 #{rank}
            </h3>
            <p className="text-xs text-gray-400">종합 점수</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-extrabold text-amber-400">
            {total_score.toFixed(1)}
          </p>
          <p className="text-[10px] text-gray-500">/ 100</p>
        </div>
      </div>

      <CardContent className="p-5">
        <div className="grid grid-cols-5 gap-2 mb-5">
          {LANE_ORDER.map((lane) => {
            const assignment = assignmentByLane[lane];
            if (!assignment) {
              return (
                <div
                  key={lane}
                  className="flex flex-col items-center gap-1.5 p-2 rounded-lg bg-gray-800/50 border border-gray-700 opacity-40"
                >
                  <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
                    {LANE_LABELS[lane]}
                  </span>
                  <div className="w-10 h-10 rounded-lg bg-gray-700 flex items-center justify-center">
                    <span className="text-gray-600 text-lg">?</span>
                  </div>
                  <span className="text-[10px] text-gray-600">미배정</span>
                </div>
              );
            }

            const playerName = assignment.player.split('#')[0];

            return (
              <div
                key={lane}
                className="flex flex-col items-center gap-1.5 p-2 rounded-lg bg-gray-800 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <span className="text-[10px] font-semibold text-amber-500 uppercase tracking-wider">
                  {LANE_LABELS[lane]}
                </span>
                <ChampionIcon
                  championName={assignment.champion}
                  championNameKo={assignment.champion_name_ko}
                  championId={assignment.champion_id}
                  size={40}
                />
                <div className="text-center">
                  <p className="text-[11px] font-semibold text-gray-200 truncate max-w-[70px]">
                    {playerName}
                  </p>
                  <p className="text-[10px] text-gray-400">
                    {assignment.champion_name_ko || assignment.champion}
                  </p>
                </div>
                <div className="flex items-center gap-1 text-[10px]">
                  <span
                    className={cn(
                      'font-medium',
                      assignment.personal_win_rate >= 0.6
                        ? 'text-emerald-400'
                        : assignment.personal_win_rate >= 0.5
                          ? 'text-amber-400'
                          : 'text-red-400'
                    )}
                  >
                    {formatWinRate(assignment.personal_win_rate, 0)}
                  </span>
                  {assignment.personal_kda != null && (
                    <span className="text-gray-500">
                      {assignment.personal_kda.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {team_analysis && (
          <TeamAnalysisChart teamAnalysis={team_analysis} />
        )}
      </CardContent>
    </Card>
  );
}
