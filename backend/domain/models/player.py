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
    champion_name_ko: str = ""
    games: int = 0
    wins: int = 0
    win_rate: float = 0.0
    kda: float = 0.0
    mastery_points: int = 0
    is_flex: bool = False
    flex_lanes: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """한글 이름 우선, 없으면 영문 이름 반환."""
        return self.champion_name_ko or self.champion_name


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
