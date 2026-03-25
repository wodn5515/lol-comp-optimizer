/**
 * @typedef {Object} Assignment
 * @property {string} player - 플레이어 Riot ID (예: "Hide on bush#KR1")
 * @property {string} lane - 라인 (TOP, JUNGLE, MID, ADC, SUPPORT)
 * @property {string} champion - 챔피언 이름 (영문)
 * @property {string} [champion_name_ko] - 챔피언 이름 (한국어)
 * @property {number} champion_id - 챔피언 ID
 * @property {number} personal_win_rate - 개인 승률
 * @property {number} personal_kda - 개인 KDA
 */

/**
 * @typedef {Object} TeamAnalysis
 * @property {number} ad_ratio - AD 비율
 * @property {number} ap_ratio - AP 비율
 * @property {boolean} has_frontline - 프론트라인 유무
 * @property {number} waveclear_score - 웨이브클리어 점수
 * @property {number} splitpush_score - 스플릿푸시 점수
 * @property {number} teamfight_score - 팀파이트 점수
 * @property {string[]} strengths - 강점
 * @property {string[]} weaknesses - 약점
 */

/**
 * @typedef {Object} Recommendation
 * @property {number} rank - 순위
 * @property {number} total_score - 종합 점수
 * @property {Assignment[]} assignments - 라인 배정
 * @property {TeamAnalysis} team_analysis - 팀 분석
 */

export {};
