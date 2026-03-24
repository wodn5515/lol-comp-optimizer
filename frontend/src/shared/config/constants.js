export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
export const DDRAGON_VERSION = import.meta.env.VITE_DDRAGON_VERSION || '14.10.1';
export const DDRAGON_CDN = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}`;
export const CHAMPION_ICON_URL = (championName) => `${DDRAGON_CDN}/img/champion/${championName}.png`;
export const PROFILE_ICON_URL = (iconId) => `${DDRAGON_CDN}/img/profileicon/${iconId}.png`;
export const TIER_ORDER = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER'];

export const TIER_COLORS = {
  IRON: '#6b6b6b',
  BRONZE: '#8c5a2e',
  SILVER: '#8e8e8e',
  GOLD: '#c89b3c',
  PLATINUM: '#3bbf9e',
  EMERALD: '#009a49',
  DIAMOND: '#576bce',
  MASTER: '#9d48e0',
  GRANDMASTER: '#e44040',
  CHALLENGER: '#f4c874',
};

export const LANE_LABELS = {
  TOP: '탑',
  JG: '정글',
  MID: '미드',
  ADC: '원딜',
  SUP: '서포터',
};

export const LANE_ICONS = {
  TOP: '🛡',
  JG: '🌿',
  MID: '⚔',
  ADC: '🏹',
  SUP: '✦',
};

export const MATCH_COUNT_OPTIONS = [10, 15, 20];
