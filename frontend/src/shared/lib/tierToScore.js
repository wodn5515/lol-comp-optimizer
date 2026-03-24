import { TIER_ORDER } from '../config/constants';

const RANK_VALUES = { IV: 0, III: 1, II: 2, I: 3 };

/**
 * 티어/랭크를 수치 점수로 변환
 * @param {string} tier - 티어 (예: "GOLD")
 * @param {string} rank - 랭크 (예: "II")
 * @param {number} lp - LP
 * @returns {number} 점수
 */
export function tierToScore(tier, rank, lp = 0) {
  if (!tier) return 0;
  const tierIndex = TIER_ORDER.indexOf(tier.toUpperCase());
  if (tierIndex === -1) return 0;
  const rankValue = RANK_VALUES[rank] || 0;
  return tierIndex * 400 + rankValue * 100 + (lp || 0);
}

/**
 * 티어/랭크를 표시 문자열로 변환
 * @param {string} tier
 * @param {string} rank
 * @param {number} lp
 * @returns {string}
 */
export function formatTier(tier, rank, lp) {
  if (!tier) return '언랭크';
  const tierKo = {
    IRON: '아이언',
    BRONZE: '브론즈',
    SILVER: '실버',
    GOLD: '골드',
    PLATINUM: '플래티넘',
    EMERALD: '에메랄드',
    DIAMOND: '다이아몬드',
    MASTER: '마스터',
    GRANDMASTER: '그랜드마스터',
    CHALLENGER: '챌린저',
  };
  const name = tierKo[tier.toUpperCase()] || tier;
  if (['MASTER', 'GRANDMASTER', 'CHALLENGER'].includes(tier.toUpperCase())) {
    return `${name} ${lp != null ? lp + 'LP' : ''}`;
  }
  return `${name} ${rank || ''} ${lp != null ? lp + 'LP' : ''}`.trim();
}
