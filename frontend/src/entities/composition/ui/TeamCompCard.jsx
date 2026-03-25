import { useState, useCallback } from 'react';
import { Card, CardContent } from '../../../shared/ui';
import { LANE_LABELS } from '../../../shared/config/constants';
import { formatWinRate } from '../../../shared/lib/formatWinRate';
import { formatCompText } from '../../../shared/lib/formatCompText';
import { cn } from '../../../shared/lib/cn';
import { ChampionIcon } from '../../champion';
import { TeamAnalysisChart } from './TeamAnalysisChart';
import { ScoreBreakdownPanel } from './ScoreBreakdownPanel';

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

export function TeamCompCard({ recommendation, defaultExpanded = true }) {
  const { rank, total_score, assignments, team_analysis, score_breakdown } = recommendation;
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      const text = formatCompText(recommendation);
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: ignore if clipboard not available
    }
  }, [recommendation]);

  const style = RANK_STYLES[rank] || RANK_STYLES[3];

  const assignmentByLane = {};
  assignments.forEach((a) => {
    assignmentByLane[a.lane] = a;
  });

  const championNames = LANE_ORDER
    .map((lane) => assignmentByLane[lane])
    .filter(Boolean)
    .map((a) => a.champion_name_ko || a.champion)
    .join(' · ');

  const compType = team_analysis?.comp_type;

  return (
    <Card className={cn('overflow-hidden', style.border)}>
      <div
        className="px-5 py-4 border-b border-gray-800 flex items-center justify-between cursor-pointer select-none hover:bg-gray-800/40 transition-colors"
        onClick={() => setIsExpanded((v) => !v)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded((v) => !v);
          }
        }}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-lg shrink-0',
              style.badge
            )}
          >
            {rank}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-gray-100">
                추천 조합 #{rank}
              </h3>
              {!isExpanded && compType && (
                <span className="text-[10px] font-medium text-gray-400 bg-gray-700 px-1.5 py-0.5 rounded shrink-0">
                  {compType}
                </span>
              )}
            </div>
            {isExpanded ? (
              <p className="text-xs text-gray-400">종합 점수</p>
            ) : (
              <p className="text-xs text-gray-500 truncate">{championNames}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {isExpanded && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleCopy();
              }}
              className={cn(
                'p-1.5 rounded-md transition-all text-gray-400 hover:text-gray-200 hover:bg-gray-700/60',
                copied && 'text-emerald-400 hover:text-emerald-400'
              )}
              title={copied ? '복사됨!' : '조합 복사'}
            >
              {copied ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                  <path d="M7 3.5A1.5 1.5 0 0 1 8.5 2h3.879a1.5 1.5 0 0 1 1.06.44l3.122 3.12A1.5 1.5 0 0 1 17 6.622V12.5a1.5 1.5 0 0 1-1.5 1.5h-1v-3.379a3 3 0 0 0-.879-2.121L10.5 5.379A3 3 0 0 0 8.379 4.5H7v-1Z" />
                  <path d="M4.5 6A1.5 1.5 0 0 0 3 7.5v9A1.5 1.5 0 0 0 4.5 18h7a1.5 1.5 0 0 0 1.5-1.5v-5.879a1.5 1.5 0 0 0-.44-1.06L9.44 6.439A1.5 1.5 0 0 0 8.378 6H4.5Z" />
                </svg>
              )}
            </button>
          )}
          <div className="text-right">
            <p className={cn('font-extrabold text-amber-400', isExpanded ? 'text-2xl' : 'text-lg')}>
              {total_score.toFixed(1)}
            </p>
            {isExpanded && <p className="text-[10px] text-gray-500">/ 100</p>}
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className={cn('w-5 h-5 text-gray-500 transition-transform duration-200', isExpanded && 'rotate-180')}
          >
            <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      <div
        className={cn(
          'grid transition-[grid-template-rows] duration-300 ease-in-out',
          isExpanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        )}
      >
        <div className="overflow-hidden">
          {score_breakdown && (
            <div className="px-5 border-b border-gray-800">
              <button
                onClick={() => setShowBreakdown((v) => !v)}
                className="w-full flex items-center justify-between py-2.5 text-xs text-gray-400 hover:text-gray-200 transition-colors"
              >
                <span className="font-medium">점수 상세</span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className={cn('w-4 h-4 transition-transform', showBreakdown && 'rotate-180')}
                >
                  <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
                </svg>
              </button>
              {showBreakdown && (
                <div className="pb-3">
                  <ScoreBreakdownPanel breakdown={score_breakdown} />
                </div>
              )}
            </div>
          )}

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
                      {assignment.is_flex && assignment.flex_lanes?.length >= 2 && (
                        <p className="text-[9px] text-violet-400 font-medium mt-0.5">
                          FLEX {assignment.flex_lanes.map(l => LANE_LABELS[l] || l).join('/')}
                        </p>
                      )}
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
        </div>
      </div>
    </Card>
  );
}
