from dataclasses import dataclass, field


@dataclass
class LaneStats:
    games: int = 0
    wins: int = 0
    win_rate: float = 0.0


@dataclass
class ChampionStats:
    champion_id: int = 0
    champion_name: str = ""
    games: int = 0
    wins: int = 0
    win_rate: float = 0.0
    kda: float = 0.0
    mastery_points: int = 0


@dataclass
class Player:
    game_name: str = ""
    tag_line: str = ""
    puuid: str = ""
    summoner_id: str = ""
    tier: str = ""
    rank: str = ""
    lp: int = 0
    profile_icon_id: int = 0
    lane_stats: dict[str, LaneStats] = field(default_factory=dict)
    top_champions: list[ChampionStats] = field(default_factory=list)
