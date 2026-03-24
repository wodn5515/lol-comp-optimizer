import pytest
from domain.models.player import Player, LaneStats
from domain.services.lane_optimizer_service import LaneOptimizerService


def make_player(
    name: str,
    lane_stats: dict[str, tuple[int, float]] | None = None,
    tag_line: str = "KR1",
) -> Player:
    """Create a Player with lane stats.

    lane_stats format: {"MID": (games, win_rate), "TOP": (games, win_rate)}
    """
    ls: dict[str, LaneStats] = {}
    if lane_stats:
        for lane, (games, win_rate) in lane_stats.items():
            wins = int(games * win_rate)
            ls[lane] = LaneStats(games=games, wins=wins, win_rate=win_rate)

    return Player(game_name=name, tag_line=tag_line, lane_stats=ls)


@pytest.fixture
def lane_optimizer() -> LaneOptimizerService:
    return LaneOptimizerService()


class TestGameCountWeight:
    """Spec section 2-2: Game count weights."""

    def test_10_plus_games_weight_1_0(self, lane_optimizer: LaneOptimizerService) -> None:
        assert lane_optimizer._game_count_weight(10) == 1.0
        assert lane_optimizer._game_count_weight(15) == 1.0
        assert lane_optimizer._game_count_weight(100) == 1.0

    def test_5_to_9_games_weight_0_8(self, lane_optimizer: LaneOptimizerService) -> None:
        assert lane_optimizer._game_count_weight(5) == 0.8
        assert lane_optimizer._game_count_weight(7) == 0.8
        assert lane_optimizer._game_count_weight(9) == 0.8

    def test_1_to_4_games_weight_0_5(self, lane_optimizer: LaneOptimizerService) -> None:
        assert lane_optimizer._game_count_weight(1) == 0.5
        assert lane_optimizer._game_count_weight(3) == 0.5
        assert lane_optimizer._game_count_weight(4) == 0.5

    def test_0_games_weight_0_1(self, lane_optimizer: LaneOptimizerService) -> None:
        assert lane_optimizer._game_count_weight(0) == 0.1


class TestLaneScore:
    def test_score_with_stats(self, lane_optimizer: LaneOptimizerService) -> None:
        player = make_player("A", lane_stats={"MID": (10, 0.7)})
        score = lane_optimizer._lane_score(player, "MID")
        assert score == pytest.approx(0.7 * 1.0, abs=0.01)

    def test_no_experience_lane_gets_penalty(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: No experience lane -> weight 0.1 (penalty)."""
        player = make_player("A", lane_stats={"MID": (10, 0.7)})
        score_mid = lane_optimizer._lane_score(player, "MID")
        score_top = lane_optimizer._lane_score(player, "TOP")
        # MID: 0.7 * 1.0 = 0.7, TOP: 0.0 * 0.1 = 0.0
        assert score_mid > score_top * 5

    def test_game_count_weight(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: Game count weights: 10+ -> 1.0, 5~9 -> 0.8, 1~4 -> 0.5."""
        p1 = make_player("A", lane_stats={"MID": (15, 0.6)})  # 15 games -> x1.0
        p2 = make_player("B", lane_stats={"MID": (3, 0.6)})   # 3 games -> x0.5
        s1 = lane_optimizer._lane_score(p1, "MID")
        s2 = lane_optimizer._lane_score(p2, "MID")
        # s1 = 0.6 * 1.0 = 0.6, s2 = 0.6 * 0.5 = 0.3
        assert s1 == pytest.approx(s2 * 2, rel=0.01)


class TestOptimize:
    def test_5_players_returns_top_assignments(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: 5 players -> 5! = 120 permutations, return top N."""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.7), "TOP": (3, 0.3)}),
            make_player("B", lane_stats={"ADC": (12, 0.65), "SUP": (5, 0.4)}),
            make_player("C", lane_stats={"JG": (15, 0.6), "MID": (5, 0.5)}),
            make_player("D", lane_stats={"TOP": (8, 0.55), "JG": (4, 0.4)}),
            make_player("E", lane_stats={"SUP": (10, 0.7), "ADC": (3, 0.45)}),
        ]
        results = lane_optimizer.optimize(players, top_n=3)
        assert len(results) == 3
        assert results[0].score >= results[1].score  # Descending order
        assert results[1].score >= results[2].score

        # Each assignment should have 5 players
        for r in results:
            assert len(r.assignments) == 5

    def test_2_players_assigns_2_lanes(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: 2 players -> 5P2 = 20 permutations, 2 lanes assigned."""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.7)}),
            make_player("B", lane_stats={"ADC": (8, 0.6)}),
        ]
        results = lane_optimizer.optimize(players, top_n=3)
        for r in results:
            assert len(r.assignments) == 2
            lanes = [a.lane for a in r.assignments]
            assert len(set(lanes)) == 2  # No duplicate lanes

    def test_3_players_assigns_3_lanes(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: 3 players -> 5P3 = 60 permutations."""
        players = [
            make_player("A", lane_stats={"TOP": (10, 0.7)}),
            make_player("B", lane_stats={"JG": (8, 0.6)}),
            make_player("C", lane_stats={"MID": (12, 0.65)}),
        ]
        results = lane_optimizer.optimize(players, top_n=5)
        assert len(results) == 5
        for r in results:
            assert len(r.assignments) == 3
            lanes = [a.lane for a in r.assignments]
            assert len(set(lanes)) == 3

    def test_4_players_assigns_4_lanes(self, lane_optimizer: LaneOptimizerService) -> None:
        """Spec: 4 players -> 5P4 = 120 permutations."""
        players = [
            make_player("A", lane_stats={"TOP": (10, 0.7)}),
            make_player("B", lane_stats={"JG": (8, 0.6)}),
            make_player("C", lane_stats={"MID": (12, 0.65)}),
            make_player("D", lane_stats={"ADC": (10, 0.6)}),
        ]
        results = lane_optimizer.optimize(players, top_n=5)
        assert len(results) == 5
        for r in results:
            assert len(r.assignments) == 4
            lanes = [a.lane for a in r.assignments]
            assert len(set(lanes)) == 4

    def test_best_assignment_optimal(self, lane_optimizer: LaneOptimizerService) -> None:
        """Best result should have each player on their best lane."""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.9)}),
            make_player("B", lane_stats={"ADC": (10, 0.8)}),
        ]
        results = lane_optimizer.optimize(players, top_n=1)
        assert results[0].assignments[0].lane == "MID"
        assert results[0].assignments[1].lane == "ADC"

    def test_empty_players(self, lane_optimizer: LaneOptimizerService) -> None:
        results = lane_optimizer.optimize([], top_n=3)
        assert results == []

    def test_no_duplicate_lanes_in_result(self, lane_optimizer: LaneOptimizerService) -> None:
        """No two players should be assigned the same lane."""
        players = [
            make_player("A", lane_stats={"MID": (10, 0.7), "TOP": (5, 0.5)}),
            make_player("B", lane_stats={"MID": (10, 0.8), "JG": (5, 0.5)}),
            make_player("C", lane_stats={"MID": (10, 0.6), "ADC": (5, 0.5)}),
        ]
        results = lane_optimizer.optimize(players, top_n=10)
        for r in results:
            lanes = [a.lane for a in r.assignments]
            assert len(set(lanes)) == len(lanes)
