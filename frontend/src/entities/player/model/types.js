/**
 * @typedef {Object} LaneStat
 * @property {number} games - 게임 수
 * @property {number} wins - 승리 수
 * @property {number} win_rate - 승률 (0~1)
 */

/**
 * @typedef {Object} ChampionStat
 * @property {number} champion_id - 챔피언 ID
 * @property {string} champion_name - 챔피언 이름 (영문)
 * @property {string} [champion_name_ko] - 챔피언 이름 (한국어)
 * @property {number} games - 게임 수
 * @property {number} wins - 승리 수
 * @property {number} win_rate - 승률 (0~1)
 * @property {number} kda - KDA
 * @property {number} mastery_points - 숙련도 점수
 */

/**
 * @typedef {Object} Player
 * @property {string} game_name - 게임 이름
 * @property {string} tag_line - 태그라인
 * @property {string|null} tier - 티어 (예: "GOLD")
 * @property {string|null} rank - 랭크 (예: "II")
 * @property {number|null} lp - LP
 * @property {number|null} profile_icon_id - 프로필 아이콘 ID
 * @property {Object.<string, LaneStat>} lane_stats - 라인별 통계
 * @property {ChampionStat[]} top_champions - 상위 챔피언 목록
 */

export {};
