import { LANE_LABELS } from '../config/constants';
import { formatWinRate } from './formatWinRate';

const LANE_ORDER = ['TOP', 'JG', 'MID', 'ADC', 'SUP'];

const LANE_ABBR = {
  TOP: 'TOP',
  JG: 'JG ',
  MID: 'MID',
  ADC: 'ADC',
  SUP: 'SUP',
};

/**
 * 추천 조합을 클립보드용 텍스트로 포맷팅
 * @param {object} recommendation - { rank, total_score, assignments, team_analysis }
 * @returns {string}
 */
export function formatCompText(recommendation) {
  const { rank, total_score, assignments, team_analysis } = recommendation;

  const assignmentByLane = {};
  assignments.forEach((a) => {
    assignmentByLane[a.lane] = a;
  });

  const compType = team_analysis?.comp_type || '';
  const header = `[LoL 조합 추천 #${rank}] 점수: ${total_score.toFixed(1)}`;
  const typeLine = compType ? `유형: ${compType}` : '';

  const lines = LANE_ORDER.map((lane) => {
    const a = assignmentByLane[lane];
    if (!a) return `${LANE_ABBR[lane]}: 미배정`;
    const playerName = a.player.split('#')[0];
    const champName = a.champion_name_ko || a.champion;
    const winRate = formatWinRate(a.personal_win_rate, 0);
    return `${LANE_ABBR[lane]}: ${playerName} → ${champName} (승률 ${winRate})`;
  });

  const parts = [header];
  if (typeLine) parts.push(typeLine);
  parts.push('');
  parts.push(...lines);

  if (team_analysis) {
    const { strengths, weaknesses } = team_analysis;
    parts.push('');
    if (strengths?.length) {
      parts.push(`강점: ${strengths.join(', ')}`);
    }
    if (weaknesses?.length) {
      parts.push(`약점: ${weaknesses.join(', ')}`);
    }
  }

  parts.push('');
  parts.push('— LoL Comp Optimizer');

  return parts.join('\n');
}
