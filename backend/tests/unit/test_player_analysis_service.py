import pytest
from domain.models.match import MatchSummary
from domain.services.player_analysis_service import PlayerAnalysisService


@pytest.fixture
def service() -> PlayerAnalysisService:
    return PlayerAnalysisService()


def make_match_summary(
    lane: str = "MID",
    win: bool = True,
    champion: str = "Zed",
    champion_id: int = 238,
    kills: int = 5,
    deaths: int = 3,
    assists: int = 4,
    match_id: str = "",
) -> MatchSummary:
    return MatchSummary(
        match_id=match_id or f"KR_{id(lane)}",
        champion_name=champion,
        champion_id=champion_id,
        lane=lane,
        win=win,
        kills=kills,
        deaths=deaths,
        assists=assists,
        cs=150,
        game_duration=1800,
    )


class TestNormalizeLane:
    def test_bottom_to_adc(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("BOTTOM") == "ADC"

    def test_utility_to_sup(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("UTILITY") == "SUP"

    def test_jungle_to_jg(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("JUNGLE") == "JG"

    def test_middle_to_mid(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("MIDDLE") == "MID"

    def test_top_stays_top(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("TOP") == "TOP"

    def test_case_insensitive(self, service: PlayerAnalysisService) -> None:
        assert service.normalize_lane("bottom") == "ADC"
        assert service.normalize_lane("utility") == "SUP"


class TestCalculateLaneStats:
    def test_lane_stats_from_matches(self, service: PlayerAnalysisService) -> None:
        """Spec section 5: Extract per-lane win rates from match history."""
        matches = [
            make_match_summary(lane="MID", win=True),
            make_match_summary(lane="MID", win=True),
            make_match_summary(lane="MID", win=False),
            make_match_summary(lane="TOP", win=True),
        ]
        stats = service.calculate_lane_stats(matches)
        assert stats["MID"].games == 3
        assert stats["MID"].wins == 2
        assert stats["MID"].win_rate == pytest.approx(0.667, abs=0.01)
        assert stats["TOP"].games == 1
        assert stats["TOP"].wins == 1
        assert stats["TOP"].win_rate == pytest.approx(1.0)

    def test_empty_matches(self, service: PlayerAnalysisService) -> None:
        stats = service.calculate_lane_stats([])
        assert stats == {}

    def test_all_losses(self, service: PlayerAnalysisService) -> None:
        matches = [
            make_match_summary(lane="ADC", win=False),
            make_match_summary(lane="ADC", win=False),
        ]
        stats = service.calculate_lane_stats(matches)
        assert stats["ADC"].games == 2
        assert stats["ADC"].wins == 0
        assert stats["ADC"].win_rate == 0.0

    def test_multiple_lanes(self, service: PlayerAnalysisService) -> None:
        matches = [
            make_match_summary(lane="TOP", win=True),
            make_match_summary(lane="JG", win=False),
            make_match_summary(lane="MID", win=True),
            make_match_summary(lane="ADC", win=True),
            make_match_summary(lane="SUP", win=False),
        ]
        stats = service.calculate_lane_stats(matches)
        assert len(stats) == 5
        for lane in ["TOP", "JG", "MID", "ADC", "SUP"]:
            assert lane in stats
            assert stats[lane].games == 1


class TestCalculateChampionStats:
    def test_top_champions_extraction(self, service: PlayerAnalysisService) -> None:
        """Spec section 5: Extract per-champion win rate / KDA from matches."""
        matches = [
            make_match_summary(champion="Zed", champion_id=238, win=True, kills=10, deaths=2, assists=5),
            make_match_summary(champion="Zed", champion_id=238, win=True, kills=8, deaths=3, assists=4),
            make_match_summary(champion="Ahri", champion_id=103, win=False, kills=3, deaths=5, assists=7),
        ]
        champs = service.calculate_champion_stats(matches)
        assert len(champs) == 2

        zed = next(c for c in champs if c.champion_name == "Zed")
        assert zed.champion_id == 238
        assert zed.games == 2
        assert zed.wins == 2
        assert zed.win_rate == 1.0
        # KDA = (10+8 + 5+4) / (2+3) = 27/5 = 5.4
        assert zed.kda == pytest.approx(5.4, abs=0.1)

        ahri = next(c for c in champs if c.champion_name == "Ahri")
        assert ahri.games == 1
        assert ahri.win_rate == 0.0
        # KDA = (3+7) / 5 = 2.0
        assert ahri.kda == pytest.approx(2.0, abs=0.1)

    def test_sorted_by_games_descending(self, service: PlayerAnalysisService) -> None:
        matches = [
            make_match_summary(champion="Zed", kills=5, deaths=1, assists=3),
            make_match_summary(champion="Zed", kills=5, deaths=1, assists=3),
            make_match_summary(champion="Zed", kills=5, deaths=1, assists=3),
            make_match_summary(champion="Ahri", champion_id=103, kills=3, deaths=2, assists=4),
        ]
        champs = service.calculate_champion_stats(matches)
        assert champs[0].champion_name == "Zed"
        assert champs[0].games == 3
        assert champs[1].champion_name == "Ahri"
        assert champs[1].games == 1

    def test_zero_deaths_kda(self, service: PlayerAnalysisService) -> None:
        """If 0 deaths, KDA = kills + assists."""
        matches = [
            make_match_summary(champion="Zed", kills=10, deaths=0, assists=5),
        ]
        champs = service.calculate_champion_stats(matches)
        assert champs[0].kda == 15.0

    def test_empty_matches(self, service: PlayerAnalysisService) -> None:
        champs = service.calculate_champion_stats([])
        assert champs == []
