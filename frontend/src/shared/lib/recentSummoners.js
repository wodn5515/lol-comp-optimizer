const STORAGE_KEY = 'lol-comp-recent-summoners';
const MAX_RECENT = 20;

export function getRecentSummoners() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

export function addRecentSummoner(riotId) {
  if (!riotId || !riotId.includes('#')) return;
  const recent = getRecentSummoners().filter((s) => s !== riotId);
  recent.unshift(riotId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));
}

export function addRecentSummoners(riotIds) {
  riotIds.forEach(addRecentSummoner);
}
