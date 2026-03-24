import { usePlayerStore } from '../../../entities/player';

export function usePlayerSummary() {
  const players = usePlayerStore((s) => s.players);

  return {
    players,
    hasPlayers: players.length > 0,
    playerCount: players.length,
  };
}
