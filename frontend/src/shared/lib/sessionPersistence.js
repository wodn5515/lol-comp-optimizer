const STORAGE_KEY = 'lol-comp-optimizer:session';
const EXPIRY_MS = 30 * 60 * 1000; // 30 minutes

export function saveSession(data) {
  try {
    const payload = {
      players: data.players,
      banned_champions: data.banned_champions,
      enemy_picks: data.enemy_picks,
      locked_picks: data.locked_picks,
      locked_positions: data.locked_positions,
      timestamp: Date.now(),
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // sessionStorage may be unavailable (private browsing, quota exceeded)
  }
}

export function loadSession() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const data = JSON.parse(raw);
    if (!data || !data.timestamp) return null;

    if (Date.now() - data.timestamp > EXPIRY_MS) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

export function clearSession() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
