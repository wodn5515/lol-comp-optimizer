import { apiClient } from '../../../shared/api/client';

/**
 * POST /api/optimize 호출
 * @param {Object} params
 * @param {string} params.apiKey - Riot API 키
 * @param {Array<{game_name: string, tag_line: string}>} params.players - 플레이어 목록
 * @param {number} params.matchCount - 매치 수 (10/15/20)
 * @param {number} params.queue - 큐 타입 (420 = 솔랭)
 * @returns {Promise<Object>} 분석 결과
 */
export async function analyzeComp({ apiKey, players, matchCount = 15 }) {
  return apiClient.post('/optimize', {
    api_key: apiKey,
    players: players.map((p) => ({
      game_name: p.game_name || p.gameName,
      tag_line: p.tag_line || p.tagLine,
    })),
    match_count: matchCount,
  });
}

/**
 * POST /api/analyze-players 호출
 * 플레이어 데이터만 분석 (밴픽 전 단계)
 * @param {Object} params
 * @param {string} params.apiKey - Riot API 키
 * @param {Array<{game_name: string, tag_line: string}>} params.players - 플레이어 목록
 * @param {number} params.matchCount - 매치 수 (10/15/20)
 * @returns {Promise<Object>} 플레이어 분석 결과
 */
export async function analyzePlayers({ apiKey, players, matchCount = 15 }) {
  return apiClient.post('/analyze-players', {
    api_key: apiKey,
    players: players.map((p) => ({
      game_name: p.game_name || p.gameName,
      tag_line: p.tag_line || p.tagLine,
    })),
    match_count: matchCount,
  });
}

/**
 * POST /api/optimize-comp 호출
 * 밴/픽 조건으로 조합 최적화
 * @param {Object} params
 * @param {Array} params.players - 분석된 플레이어 데이터
 * @param {Array<string>} params.bannedChampions - 밴된 챔피언 목록
 * @param {Array<string>} params.enemyPicks - 적 팀 픽 목록
 * @param {Object} params.lockedPicks - 고정 픽 { "playerName#tag": "ChampionName" }
 * @returns {Promise<Object>} 최적화 결과
 */
export async function optimizeComp({ players, bannedChampions = [], enemyPicks = [], lockedPicks = {} }) {
  return apiClient.post('/optimize-comp', {
    players,
    banned_champions: bannedChampions,
    enemy_picks: enemyPicks,
    locked_picks: lockedPicks,
  });
}
