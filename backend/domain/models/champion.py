from dataclasses import dataclass, field


@dataclass
class ChampionAttributes:
    champion_id: int = 0
    champion_name: str = ""
    damage_type: str = "AD"  # "AD" | "AP" | "HYBRID"
    role_tags: list[str] = field(default_factory=list)
    waveclear: int = 3
    splitpush: int = 3
    teamfight: int = 3
    engage: int = 3
    peel: int = 1
    poke: int = 3       # 1~5
    pick: int = 3       # 1~5
    burst: int = 3      # 1~5
    primary_lanes: list[str] = field(default_factory=lambda: ["TOP", "MID"])  # lanes this champion naturally plays
    source: str = "MANUAL"  # "MANUAL" | "AUTO"
