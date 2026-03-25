from dataclasses import dataclass, field


@dataclass
class Assignment:
    player_game_name: str = ""
    player_tag_line: str = ""
    lane: str = ""  # TOP, JG, MID, ADC, SUP
    champion_name: str = ""
    champion_name_ko: str = ""
    champion_id: int = 0
    personal_win_rate: float = 0.0
    personal_kda: float = 0.0
    personal_games: int = 0
    mastery_points: int = 0

    @property
    def display_name(self) -> str:
        """한글 이름 우선, 없으면 영문 이름 반환."""
        return self.champion_name_ko or self.champion_name


@dataclass
class TeamAnalysis:
    ad_ratio: float = 0.0
    ap_ratio: float = 0.0
    has_frontline: bool = False
    waveclear_score: int = 0
    splitpush_score: int = 0
    teamfight_score: int = 0
    engage_score: int = 0
    peel_score: int = 0
    poke_score: int = 0
    pick_score: int = 0
    burst_score: int = 0
    comp_type: str = ""           # e.g. "이니시 + 한타 조합"
    strategy_guide: str = ""      # How to play this comp
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    penalties: dict[str, int] = field(default_factory=dict)
    # Per-champion stat contributions: { "teamfight": [{"champion": "Orianna", "value": 5}, ...], ... }
    stat_contributions: dict[str, list[dict]] = field(default_factory=dict)


@dataclass
class LaneAssignment:
    assignments: list[Assignment] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Composition:
    rank: int = 0
    total_score: float = 0.0
    assignments: list[Assignment] = field(default_factory=list)
    team_analysis: TeamAnalysis = field(default_factory=TeamAnalysis)
