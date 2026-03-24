import { create } from 'zustand';

const MIN_PLAYERS = 2;
const MAX_PLAYERS = 5;

const createEmptyInput = () => ({
  id: crypto.randomUUID(),
  rawInput: '',
});

/**
 * 멀티서치 텍스트에서 Riot ID(이름#태그) 목록 추출
 *
 * 지원 형식:
 * 1) 로비 채팅: "미 키 #0313 님이 로비에 참가하셨습니다."
 * 2) 쉼표 구분: "미 키 #0313,dlwldms #iuiu,Daemi #Arneb"
 * 3) 줄바꿈 구분: 한 줄에 하나씩
 *
 * # 앞뒤 공백 허용: "미 키 #0313" → gameName="미 키", tagLine="0313"
 */
function parseMultiSearch(text) {
  const results = [];

  // 먼저 쉼표가 있으면 쉼표로 분리, 없으면 줄바꿈으로 분리
  const hasComma = text.includes(',');
  const chunks = hasComma
    ? text.split(',')
    : text.split('\n');

  for (const raw of chunks) {
    const chunk = raw.trim();
    if (!chunk) continue;

    // "님이 ..." 패턴 제거 (로비 채팅)
    // "미 키 #0313 님이 로비에 참가하셨습니다." → "미 키 #0313"
    const lobbyMatch = chunk.match(/^(.+?#\s*\S+?)\s*님이\s/);
    if (lobbyMatch) {
      results.push(normalizeRiotId(lobbyMatch[1]));
      continue;
    }

    // "joined" 패턴 (영어)
    const joinMatch = chunk.match(/^(.+?#\s*\S+?)\s*joined\s/i);
    if (joinMatch) {
      results.push(normalizeRiotId(joinMatch[1]));
      continue;
    }

    // 패턴 없으면 그대로 사용 (이미 이름#태그 형식이거나 이름만)
    results.push(normalizeRiotId(chunk));
  }

  return results.slice(0, MAX_PLAYERS);
}

/**
 * "미 키 #0313" → "미 키#0313" (# 앞뒤 공백 정리)
 */
function normalizeRiotId(raw) {
  const str = raw.trim();
  // # 기준으로 분리 (마지막 # 사용)
  const hashIdx = str.lastIndexOf('#');
  if (hashIdx === -1) return str;
  const name = str.slice(0, hashIdx).trim();
  const tag = str.slice(hashIdx + 1).trim();
  return `${name}#${tag}`;
}

export const usePlayerListStore = create((set, get) => ({
  playerInputs: [createEmptyInput(), createEmptyInput()],

  addPlayerInput: () => {
    const { playerInputs } = get();
    if (playerInputs.length >= MAX_PLAYERS) return;
    set({ playerInputs: [...playerInputs, createEmptyInput()] });
  },

  removePlayerInput: (id) => {
    const { playerInputs } = get();
    if (playerInputs.length <= MIN_PLAYERS) return;
    set({ playerInputs: playerInputs.filter((p) => p.id !== id) });
  },

  updatePlayerInput: (id, value) => {
    set((state) => ({
      playerInputs: state.playerInputs.map((p) =>
        p.id === id ? { ...p, rawInput: value } : p
      ),
    }));
  },

  parseRiotId: (rawInput) => {
    const hashIndex = rawInput.lastIndexOf('#');
    if (hashIndex === -1) return { gameName: rawInput.trim(), tagLine: '' };
    return {
      gameName: rawInput.slice(0, hashIndex).trim(),
      tagLine: rawInput.slice(hashIndex + 1).trim(),
    };
  },

  getValidPlayers: () => {
    const { playerInputs, parseRiotId } = get();
    return playerInputs
      .map((p) => ({ ...parseRiotId(p.rawInput), id: p.id }))
      .filter((p) => p.gameName && p.tagLine);
  },

  canAdd: () => get().playerInputs.length < MAX_PLAYERS,
  canRemove: () => get().playerInputs.length > MIN_PLAYERS,
  playerCount: () => get().playerInputs.length,

  fillFromMultiSearch: (text) => {
    const parsed = parseMultiSearch(text);
    if (parsed.length === 0) return;

    const newInputs = parsed.map((riotId) => ({
      id: crypto.randomUUID(),
      rawInput: riotId,
    }));

    while (newInputs.length < MIN_PLAYERS) {
      newInputs.push(createEmptyInput());
    }

    set({ playerInputs: newInputs });
  },

  resetInputs: () => {
    set({ playerInputs: [createEmptyInput(), createEmptyInput()] });
  },
}));
