from domain.models.match import MatchSummary
from domain.models.player import LaneStats, ChampionStats


# Riot API position names -> our lane names
_LANE_MAP: dict[str, str] = {
    "TOP": "TOP",
    "JUNGLE": "JG",
    "MIDDLE": "MID",
    "BOTTOM": "ADC",
    "UTILITY": "SUP",
    # Already normalized forms (from our own data)
    "JG": "JG",
    "MID": "MID",
    "ADC": "ADC",
    "SUP": "SUP",
}


class PlayerAnalysisService:
    """Pure service for analyzing player match data. No external dependencies."""

    def normalize_lane(self, position: str) -> str:
        """Map Riot API positions to our lane names.

        BOTTOM -> ADC, UTILITY -> SUP, JUNGLE -> JG, MIDDLE -> MID, TOP -> TOP
        """
        return _LANE_MAP.get(position.upper(), position.upper())

    def calculate_lane_stats(self, matches: list[MatchSummary]) -> dict[str, LaneStats]:
        """Group matches by lane, calculate games/wins/win_rate."""
        lane_data: dict[str, dict[str, int]] = {}

        for match in matches:
            lane = match.lane
            if lane not in lane_data:
                lane_data[lane] = {"games": 0, "wins": 0}
            lane_data[lane]["games"] += 1
            if match.win:
                lane_data[lane]["wins"] += 1

        result: dict[str, LaneStats] = {}
        for lane, data in lane_data.items():
            games = data["games"]
            wins = data["wins"]
            win_rate = wins / games if games > 0 else 0.0
            result[lane] = LaneStats(games=games, wins=wins, win_rate=win_rate)

        return result

    def calculate_champion_stats(self, matches: list[MatchSummary]) -> list[ChampionStats]:
        """Group matches by champion, calculate games/wins/win_rate/kda."""
        champ_data: dict[str, dict] = {}

        for match in matches:
            name = match.champion_name
            if name not in champ_data:
                champ_data[name] = {
                    "champion_id": match.champion_id,
                    "games": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                }
            champ_data[name]["games"] += 1
            if match.win:
                champ_data[name]["wins"] += 1
            champ_data[name]["kills"] += match.kills
            champ_data[name]["deaths"] += match.deaths
            champ_data[name]["assists"] += match.assists

        result: list[ChampionStats] = []
        for name, data in champ_data.items():
            games = data["games"]
            wins = data["wins"]
            win_rate = wins / games if games > 0 else 0.0
            deaths = data["deaths"]
            kda = (data["kills"] + data["assists"]) / deaths if deaths > 0 else float(data["kills"] + data["assists"])
            result.append(
                ChampionStats(
                    champion_id=data["champion_id"],
                    champion_name=name,
                    games=games,
                    wins=wins,
                    win_rate=win_rate,
                    kda=round(kda, 2),
                )
            )

        # Sort by games descending
        result.sort(key=lambda c: c.games, reverse=True)
        return result
