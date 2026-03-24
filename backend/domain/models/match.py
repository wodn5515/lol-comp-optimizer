from dataclasses import dataclass


@dataclass
class MatchSummary:
    match_id: str = ""
    champion_name: str = ""
    champion_id: int = 0
    lane: str = ""  # TOP, JG, MID, ADC, SUP
    win: bool = False
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    cs: int = 0
    game_duration: int = 0
