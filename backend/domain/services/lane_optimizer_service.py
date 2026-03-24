from itertools import permutations
from domain.models.player import Player
from domain.models.composition import Assignment, LaneAssignment


LANES: list[str] = ["TOP", "JG", "MID", "ADC", "SUP"]


class LaneOptimizerService:
    """Optimizes lane assignments for a group of players via exhaustive search.

    No external dependencies -- pure business logic.
    """

    def _game_count_weight(self, games: int) -> float:
        """Return weight multiplier based on game count.

        10+ games -> 1.0
        5-9 games -> 0.8
        1-4 games -> 0.5
        0 games   -> 0.1
        """
        if games >= 10:
            return 1.0
        elif games >= 5:
            return 0.8
        elif games >= 1:
            return 0.5
        else:
            return 0.1

    def _lane_score(self, player: Player, lane: str) -> float:
        """Calculate score for a player in a given lane.

        score = win_rate * game_count_weight
        """
        lane_stats = player.lane_stats.get(lane)
        if lane_stats is None or lane_stats.games == 0:
            return 0.0 * self._game_count_weight(0)  # 0.0 * 0.1 = 0.0
        return lane_stats.win_rate * self._game_count_weight(lane_stats.games)

    def optimize(
        self,
        players: list[Player],
        top_n: int = 5,
        lane_constraints: dict[str, list[str]] | None = None,
    ) -> list[LaneAssignment]:
        """Find the best lane assignments for the given players.

        For N players, generates permutations of N lanes from 5 (nPr).
        Returns top_n results sorted by score descending.

        Args:
            lane_constraints: Optional dict mapping "gameName#tagLine" to list of
                allowed lanes. If set, only those lanes are valid for that player.
                Example: {"Faker#KR1": ["MID", "TOP"]} means Faker can only go MID or TOP.
        """
        n = len(players)
        if n == 0:
            return []
        if n > 5:
            n = 5
            players = players[:5]

        constraints = lane_constraints or {}

        all_assignments: list[LaneAssignment] = []

        # Generate all permutations of n lanes from 5 available lanes
        for lane_perm in permutations(LANES, n):
            total_score = 0.0
            assignments: list[Assignment] = []
            valid = True

            for i, player in enumerate(players):
                lane = lane_perm[i]
                player_key = f"{player.game_name}#{player.tag_line}"

                # Check lane constraint
                if player_key in constraints:
                    allowed_lanes = constraints[player_key]
                    if lane not in allowed_lanes:
                        valid = False
                        break

                score = self._lane_score(player, lane)
                total_score += score
                assignments.append(
                    Assignment(
                        player_game_name=player.game_name,
                        player_tag_line=player.tag_line,
                        lane=lane,
                    )
                )

            if not valid:
                continue

            all_assignments.append(
                LaneAssignment(assignments=assignments, score=total_score)
            )

        # Sort by score descending
        all_assignments.sort(key=lambda la: la.score, reverse=True)

        return all_assignments[:top_n]
