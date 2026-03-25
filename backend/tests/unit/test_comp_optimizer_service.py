import pytest
from domain.models.champion import ChampionAttributes
from domain.models.composition import Assignment
from domain.services.comp_optimizer_service import CompOptimizerService


def make_champ(
    name: str = "TestChamp",
    damage_type: str = "AD",
    role_tags: list[str] | None = None,
    primary_lanes: list[str] | None = None,
    waveclear: int = 3,
    splitpush: int = 3,
    teamfight: int = 3,
    engage: int = 3,
    peel: int = 1,
    poke: int = 3,
    pick: int = 3,
    burst: int = 3,
    champion_id: int = 0,
    play_tips: str = "",
    meta_tier: dict[str, str] | None = None,
    champion_name_ko: str = "",
) -> ChampionAttributes:
    return ChampionAttributes(
        champion_id=champion_id,
        champion_name=name,
        champion_name_ko=champion_name_ko,
        damage_type=damage_type,
        role_tags=role_tags or ["BRUISER"],
        primary_lanes=primary_lanes or ["TOP", "MID", "JG", "ADC", "SUP"],
        waveclear=waveclear,
        splitpush=splitpush,
        teamfight=teamfight,
        engage=engage,
        peel=peel,
        poke=poke,
        pick=pick,
        burst=burst,
        play_tips=play_tips,
        meta_tier=meta_tier or {},
    )


def make_assignment(
    name: str = "Player",
    lane: str = "MID",
    champion_name: str = "Zed",
    win_rate: float = 0.6,
    kda: float = 3.0,
    games: int = 10,
) -> Assignment:
    return Assignment(
        player_game_name=name,
        player_tag_line="KR1",
        lane=lane,
        champion_name=champion_name,
        personal_win_rate=win_rate,
        personal_kda=kda,
        personal_games=games,
    )


def make_5_assignments(
    win_rate: float = 0.6, games: int = 10
) -> list[Assignment]:
    lanes = ["TOP", "JG", "MID", "ADC", "SUP"]
    names = ["P1", "P2", "P3", "P4", "P5"]
    champs = ["Aatrox", "LeeSin", "Viktor", "Jinx", "Thresh"]
    return [
        make_assignment(
            name=n, lane=l, champion_name=c, win_rate=win_rate, games=games
        )
        for n, l, c in zip(names, lanes, champs)
    ]


@pytest.fixture
def comp_optimizer() -> CompOptimizerService:
    return CompOptimizerService()


class TestPenalties:
    def test_full_ad_penalty(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Full AD composition -> -30 points penalty."""
        ad_champs = [
            make_champ("Zed", damage_type="AD", role_tags=["ASSASSIN"]),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"]),
            make_champ("Jayce", damage_type="AD", role_tags=["BRUISER"]),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"]),
            make_champ("Thresh", damage_type="AD", role_tags=["SUPPORT"]),
        ]
        assignments = make_5_assignments()
        score_all_ad = comp_optimizer.calculate_score(assignments, ad_champs)

        mixed_champs = [
            make_champ("Zed", damage_type="AD", role_tags=["ASSASSIN"]),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"]),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"]),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"]),
            make_champ("Thresh", damage_type="AD", role_tags=["SUPPORT"]),
        ]
        score_mixed = comp_optimizer.calculate_score(assignments, mixed_champs)
        # The mixed comp should score higher due to no full AD penalty (-30)
        assert score_mixed > score_all_ad + 20

    def test_full_ap_penalty(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Full AP composition -> -30 points penalty."""
        ap_champs = [
            make_champ("Akali", damage_type="AP", role_tags=["ASSASSIN"]),
            make_champ("Evelynn", damage_type="AP", role_tags=["ASSASSIN"]),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"]),
            make_champ("Syndra", damage_type="AP", role_tags=["MAGE"]),
            make_champ("Lux", damage_type="AP", role_tags=["SUPPORT"]),
        ]
        assignments = make_5_assignments()
        penalties = comp_optimizer._calculate_penalties(ap_champs)
        assert "full_ap" in penalties
        assert penalties["full_ap"] == -30

    def test_no_frontline_penalty_for_engage_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: No frontline penalty (-25) applies for comps that NEED frontline (이니시, 한타, 프로텍트).
        Engage comp (engage>=15) without frontline should get -25 penalty."""
        # Engage comp without frontline: engage >= 15, no TANK/BRUISER
        no_frontline_engage = [
            make_champ("Zed", damage_type="AD", role_tags=["ASSASSIN"], engage=5, poke=1, pick=1, burst=1),
            make_champ("Nidalee", damage_type="AP", role_tags=["MAGE"], engage=4, poke=1, pick=1, burst=1),
            make_champ("LeBlanc", damage_type="AP", role_tags=["ASSASSIN"], engage=3, poke=1, pick=1, burst=1),
            make_champ("Ezreal", damage_type="AD", role_tags=["MARKSMAN"], engage=2, poke=1, pick=1, burst=1),
            make_champ("Lux", damage_type="AP", role_tags=["MAGE"], engage=3, poke=1, pick=1, burst=1),
        ]
        # engage = 5+4+3+2+3 = 17 >= 15 → 이니시 comp → needs frontline
        penalties = comp_optimizer._calculate_penalties(no_frontline_engage)
        assert "no_frontline" in penalties
        assert penalties["no_frontline"] == -25

    def test_no_frontline_penalty_skipped_for_poke_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: No frontline penalty does NOT apply for comps that don't need it (포킹, 픽, 폭딜, 다이브)."""
        # Poke comp without frontline: poke >= 14, no TANK/BRUISER
        poke_no_frontline = [
            make_champ("Jayce", damage_type="AD", role_tags=["MARKSMAN"], poke=4, engage=1, pick=1, burst=1),
            make_champ("Xerath", damage_type="AP", role_tags=["MAGE"], poke=5, engage=1, pick=1, burst=1),
            make_champ("Zoe", damage_type="AP", role_tags=["MAGE"], poke=4, engage=1, pick=1, burst=1),
            make_champ("Ezreal", damage_type="AD", role_tags=["MARKSMAN"], poke=3, engage=1, pick=1, burst=1),
            make_champ("Lux", damage_type="AP", role_tags=["MAGE"], poke=3, engage=1, pick=1, burst=1),
        ]
        # poke = 4+5+4+3+3 = 19 >= 14 → 포킹 comp → no frontline penalty
        penalties = comp_optimizer._calculate_penalties(poke_no_frontline)
        assert "no_frontline" not in penalties

    def test_no_frontline_penalty_skipped_for_balanced_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Balanced comp (no detected type) should NOT get frontline penalty."""
        balanced_no_frontline = [
            make_champ("Zed", damage_type="AD", role_tags=["ASSASSIN"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("Nidalee", damage_type="AP", role_tags=["MAGE"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("LeBlanc", damage_type="AP", role_tags=["ASSASSIN"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("Ezreal", damage_type="AD", role_tags=["MARKSMAN"], engage=1, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=1),
            make_champ("Lux", damage_type="AP", role_tags=["MAGE"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
        ]
        penalties = comp_optimizer._calculate_penalties(balanced_no_frontline)
        assert "no_frontline" not in penalties

    def test_waveclear_low_penalty(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Waveclear total < 10 -> -10 points."""
        low_waveclear_champs = [
            make_champ("A", waveclear=1, role_tags=["BRUISER"]),
            make_champ("B", waveclear=2, role_tags=["BRUISER"]),
            make_champ("C", waveclear=2, role_tags=["MAGE"], damage_type="AP"),
            make_champ("D", waveclear=2, role_tags=["MARKSMAN"]),
            make_champ("E", waveclear=2, role_tags=["SUPPORT"], damage_type="AP"),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, low_waveclear_champs)
        assert analysis.waveclear_score == 9
        assert "low_waveclear" in analysis.penalties
        assert analysis.penalties["low_waveclear"] == -10

    def test_no_penalty_for_balanced_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """Balanced composition should have no penalties."""
        balanced_champs = [
            make_champ("Ornn", damage_type="AP", role_tags=["TANK"], waveclear=4, teamfight=5, engage=5),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], waveclear=3, teamfight=3, engage=4),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], waveclear=5, teamfight=4),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], waveclear=3, teamfight=4),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"], engage=4, peel=4, waveclear=1),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, balanced_champs)
        assert len(analysis.penalties) == 0


class TestScoreWeights:
    def test_balanced_comp_high_score(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Balanced comp (AD/AP, frontline, waveclear ok) -> high score, no penalties."""
        balanced_champs = [
            make_champ("Ornn", damage_type="AP", role_tags=["TANK"], waveclear=4, teamfight=5, engage=5),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], waveclear=3, teamfight=3, engage=4),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], waveclear=5, teamfight=4),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], waveclear=3, teamfight=4),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"], engage=4, peel=4, waveclear=1),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, balanced_champs)
        assert analysis.ad_ratio == pytest.approx(0.4, abs=0.1)
        assert analysis.has_frontline is True
        assert analysis.waveclear_score >= 10
        assert len(analysis.penalties) == 0

    def test_personal_mastery_weight_25pct(self, comp_optimizer: CompOptimizerService) -> None:
        """Spec: Personal mastery weight is 25% (was 30%, reduced for meta_tier)."""
        balanced_champs = [
            make_champ("Ornn", damage_type="AP", role_tags=["TANK"], waveclear=3, teamfight=4),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], waveclear=3, teamfight=3),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], waveclear=4, teamfight=3),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], waveclear=3, teamfight=3),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"], waveclear=2, teamfight=3),
        ]

        high_mastery = make_5_assignments(win_rate=0.9, games=15)
        low_mastery = make_5_assignments(win_rate=0.3, games=15)

        score_high = comp_optimizer.calculate_score(high_mastery, balanced_champs)
        score_low = comp_optimizer.calculate_score(low_mastery, balanced_champs)

        diff = score_high - score_low
        # 25% weight * 100 * (0.9 - 0.3) * mastery_factor(1.0) / 1.3 = ~11.5
        assert diff == pytest.approx(11.5, abs=5)


class TestAnalyze:
    def test_ad_ap_ratio(self, comp_optimizer: CompOptimizerService) -> None:
        champs = [
            make_champ("A", damage_type="AD"),
            make_champ("B", damage_type="AD"),
            make_champ("C", damage_type="AP"),
            make_champ("D", damage_type="AP"),
            make_champ("E", damage_type="AP"),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert analysis.ad_ratio == pytest.approx(0.4, abs=0.01)
        assert analysis.ap_ratio == pytest.approx(0.6, abs=0.01)

    def test_hybrid_counts_as_both(self, comp_optimizer: CompOptimizerService) -> None:
        champs = [
            make_champ("A", damage_type="HYBRID"),
            make_champ("B", damage_type="AD"),
            make_champ("C", damage_type="AP"),
            make_champ("D", damage_type="AD"),
            make_champ("E", damage_type="AP"),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        # HYBRID = 0.5 AD + 0.5 AP, so total AD = 2.5, AP = 2.5
        assert analysis.ad_ratio == pytest.approx(0.5, abs=0.01)
        assert analysis.ap_ratio == pytest.approx(0.5, abs=0.01)

    def test_frontline_detection(self, comp_optimizer: CompOptimizerService) -> None:
        with_tank = [make_champ("A", role_tags=["TANK"])]
        without_tank = [make_champ("A", role_tags=["ASSASSIN"])]
        with_bruiser = [make_champ("A", role_tags=["BRUISER"])]

        a = [make_assignment()]
        assert comp_optimizer.analyze(a, with_tank).has_frontline is True
        assert comp_optimizer.analyze(a, without_tank).has_frontline is False
        assert comp_optimizer.analyze(a, with_bruiser).has_frontline is True

    def test_strengths_and_weaknesses(self, comp_optimizer: CompOptimizerService) -> None:
        strong_comp = [
            make_champ("A", damage_type="AD", role_tags=["TANK"], waveclear=5, teamfight=5, engage=5, peel=3),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], waveclear=4, teamfight=4, engage=4, peel=3),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], waveclear=5, teamfight=5, engage=3, peel=3),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], waveclear=4, teamfight=4, engage=1, peel=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], waveclear=2, teamfight=3, engage=3, peel=5),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, strong_comp)
        assert "안정적인 프론트라인" in analysis.strengths
        assert "우수한 웨이브클리어" in analysis.strengths

    def test_empty_composition(self, comp_optimizer: CompOptimizerService) -> None:
        analysis = comp_optimizer.analyze([], [])
        assert analysis.ad_ratio == 0.0
        assert analysis.ap_ratio == 0.0
        assert analysis.has_frontline is False


class TestCompArchetypes:
    def test_comp_type_engage(self, comp_optimizer: CompOptimizerService) -> None:
        """engage >= 15 -> comp_type contains '이니시'."""
        champs = [
            make_champ("A", damage_type="AD", role_tags=["TANK"], engage=5, poke=1, pick=1, burst=1),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], engage=4, poke=1, pick=1, burst=1),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], engage=3, poke=1, pick=1, burst=1),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], engage=2, poke=1, pick=1, burst=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], engage=3, poke=1, pick=1, burst=1),
        ]
        # engage total = 5+4+3+2+3 = 17 >= 15
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert "이니시" in analysis.comp_type

    def test_comp_type_poke(self, comp_optimizer: CompOptimizerService) -> None:
        """poke >= 14 -> comp_type contains '포킹'."""
        champs = [
            make_champ("A", damage_type="AD", role_tags=["BRUISER"], poke=3, engage=1, pick=1, burst=1),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], poke=3, engage=1, pick=1, burst=1),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], poke=4, engage=1, pick=1, burst=1),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], poke=2, engage=1, pick=1, burst=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], poke=3, engage=1, pick=1, burst=1),
        ]
        # poke total = 3+3+4+2+3 = 15 >= 14
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert "포킹" in analysis.comp_type

    def test_comp_type_multiple(self, comp_optimizer: CompOptimizerService) -> None:
        """Both engage >= 15 and teamfight >= 18 -> combined type."""
        champs = [
            make_champ("A", damage_type="AD", role_tags=["TANK"], engage=5, teamfight=5, poke=1, pick=1, burst=1),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], engage=4, teamfight=4, poke=1, pick=1, burst=1),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], engage=3, teamfight=4, poke=1, pick=1, burst=1),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], engage=1, teamfight=3, poke=1, pick=1, burst=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], engage=3, teamfight=4, poke=1, pick=1, burst=1),
        ]
        # engage = 5+4+3+1+3 = 16 >= 15
        # teamfight = 5+4+4+3+4 = 20 >= 18
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert "이니시" in analysis.comp_type
        assert "한타" in analysis.comp_type
        assert "+" in analysis.comp_type

    def test_strategy_guide_not_empty(self, comp_optimizer: CompOptimizerService) -> None:
        """Strategy guide is generated when comp type is detected."""
        champs = [
            make_champ("A", damage_type="AD", role_tags=["TANK"], engage=5, poke=1, pick=1, burst=1),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], engage=4, poke=1, pick=1, burst=1),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], engage=3, poke=1, pick=1, burst=1),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], engage=2, poke=1, pick=1, burst=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], engage=3, poke=1, pick=1, burst=1),
        ]
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert analysis.strategy_guide != ""
        assert "이니시" in analysis.strategy_guide

    def test_comp_type_balanced_fallback(self, comp_optimizer: CompOptimizerService) -> None:
        """No thresholds met -> '균형 조합'."""
        champs = [
            make_champ("A", damage_type="AD", role_tags=["BRUISER"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("B", damage_type="AD", role_tags=["BRUISER"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("C", damage_type="AP", role_tags=["MAGE"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
            make_champ("D", damage_type="AD", role_tags=["MARKSMAN"], engage=1, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=1),
            make_champ("E", damage_type="AP", role_tags=["SUPPORT"], engage=2, poke=2, pick=2, burst=2, teamfight=3, splitpush=2, peel=2),
        ]
        # engage=9, poke=10, pick=10, burst=10, teamfight=15, splitpush=10, peel=9
        # None reach thresholds
        assignments = make_5_assignments()
        analysis = comp_optimizer.analyze(assignments, champs)
        assert analysis.comp_type == "균형 조합"
        # Strategy guide may contain champion roles guide even for balanced comps
        if analysis.strategy_guide:
            assert "챔피언별 역할" in analysis.strategy_guide


class TestPrimaryLanesFiltering:
    def test_champion_filtered_by_primary_lanes(self, comp_optimizer: CompOptimizerService) -> None:
        """Poppy (primary_lanes: TOP, JG, SUP) should NOT be recommended for ADC."""
        from domain.models.player import Player, ChampionStats
        from domain.models.composition import LaneAssignment, Assignment

        # Create a player whose only champion is Poppy
        player = Player(
            game_name="TestPlayer",
            tag_line="KR1",
            lane_stats={},
            top_champions=[
                ChampionStats(champion_name="Poppy", champion_id=78, games=10, wins=7, win_rate=0.7, kda=3.0),
                ChampionStats(champion_name="Jinx", champion_id=222, games=5, wins=3, win_rate=0.6, kda=2.5),
            ],
        )

        champion_attrs_map = {
            "Poppy": make_champ("Poppy", damage_type="AD", role_tags=["TANK"], primary_lanes=["TOP", "JG", "SUP"], champion_id=78),
            "Jinx": make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], primary_lanes=["ADC"], champion_id=222),
        }

        # Lane assignment puts the player in ADC
        lane_assignment = LaneAssignment(
            assignments=[
                Assignment(
                    player_game_name="TestPlayer",
                    player_tag_line="KR1",
                    lane="ADC",
                ),
            ],
            score=1.0,
        )

        compositions = comp_optimizer.optimize(
            players=[player],
            lane_assignments=[lane_assignment],
            champion_attrs_map=champion_attrs_map,
            top_n=5,
        )

        # Poppy should NOT be assigned ADC in any composition
        for comp in compositions:
            for a in comp.assignments:
                if a.lane == "ADC":
                    assert a.champion_name != "Poppy", \
                        "Poppy should not be recommended for ADC (primary_lanes: TOP, JG, SUP)"

        # Jinx should be the ADC pick
        assert len(compositions) >= 1
        assert compositions[0].assignments[0].champion_name == "Jinx"

    def test_skip_lane_assignment_if_no_champion_fits(self, comp_optimizer: CompOptimizerService) -> None:
        """If no champions fit the assigned lane, skip and try next lane assignment."""
        from domain.models.player import Player, ChampionStats
        from domain.models.composition import LaneAssignment, Assignment

        player = Player(
            game_name="TestPlayer",
            tag_line="KR1",
            lane_stats={},
            top_champions=[
                ChampionStats(champion_name="Aatrox", champion_id=266, games=10, wins=7, win_rate=0.7, kda=3.0),
            ],
        )

        champion_attrs_map = {
            # Aatrox only plays TOP, but player is assigned MID → no fit, skip this assignment
            "Aatrox": make_champ("Aatrox", damage_type="AD", role_tags=["BRUISER"], primary_lanes=["TOP"], champion_id=266),
        }

        lane_assignments = [
            # Assignment 1: MID → no fit → skip
            LaneAssignment(
                assignments=[Assignment(player_game_name="TestPlayer", player_tag_line="KR1", lane="MID")],
                score=1.0,
            ),
            # Assignment 2: TOP → fits → use
            LaneAssignment(
                assignments=[Assignment(player_game_name="TestPlayer", player_tag_line="KR1", lane="TOP")],
                score=0.8,
            ),
        ]

        compositions = comp_optimizer.optimize(
            players=[player],
            lane_assignments=lane_assignments,
            champion_attrs_map=champion_attrs_map,
            top_n=5,
        )

        # Skipped MID (no fit), fell back to TOP assignment
        assert len(compositions) >= 1
        assert compositions[0].assignments[0].lane == "TOP"
        assert compositions[0].assignments[0].champion_name == "Aatrox"


class TestMetaTier:
    def test_meta_tier_score_all_s_tier(self, comp_optimizer: CompOptimizerService) -> None:
        """All S-tier champions should get perfect meta score (100)."""
        assignments = [
            make_assignment(name="P1", lane="TOP", champion_name="Fiora"),
            make_assignment(name="P2", lane="JG", champion_name="LeeSin"),
            make_assignment(name="P3", lane="MID", champion_name="Zed"),
            make_assignment(name="P4", lane="ADC", champion_name="Caitlyn"),
            make_assignment(name="P5", lane="SUP", champion_name="Thresh"),
        ]
        champion_attrs_map = {
            "Fiora": make_champ("Fiora", meta_tier={"TOP": "S"}),
            "LeeSin": make_champ("LeeSin", meta_tier={"JG": "S"}),
            "Zed": make_champ("Zed", meta_tier={"MID": "S"}),
            "Caitlyn": make_champ("Caitlyn", meta_tier={"ADC": "S"}),
            "Thresh": make_champ("Thresh", meta_tier={"SUP": "S"}),
        }
        score = comp_optimizer._meta_tier_score(assignments, champion_attrs_map)
        assert score == 100.0

    def test_meta_tier_score_all_d_tier(self, comp_optimizer: CompOptimizerService) -> None:
        """All D-tier champions should get low meta score (20)."""
        assignments = [
            make_assignment(name="P1", lane="TOP", champion_name="A"),
        ]
        champion_attrs_map = {
            "A": make_champ("A", meta_tier={"TOP": "D"}),
        }
        score = comp_optimizer._meta_tier_score(assignments, champion_attrs_map)
        assert score == 20.0

    def test_meta_tier_default_b_for_missing(self, comp_optimizer: CompOptimizerService) -> None:
        """Champions without meta_tier data should default to B (60)."""
        assignments = [
            make_assignment(name="P1", lane="TOP", champion_name="Unknown"),
        ]
        champion_attrs_map: dict = {}
        score = comp_optimizer._meta_tier_score(assignments, champion_attrs_map)
        assert score == 60.0

    def test_meta_tier_off_lane_defaults_to_b(self, comp_optimizer: CompOptimizerService) -> None:
        """Champion played in a lane not in their meta_tier defaults to B (60)."""
        assignments = [
            make_assignment(name="P1", lane="SUP", champion_name="Zed"),
        ]
        champion_attrs_map = {
            "Zed": make_champ("Zed", meta_tier={"MID": "S"}),
        }
        score = comp_optimizer._meta_tier_score(assignments, champion_attrs_map)
        assert score == 60.0  # B tier default for off-meta lane

    def test_meta_tier_affects_total_score(self, comp_optimizer: CompOptimizerService) -> None:
        """Meta tier 10% weight should affect total score."""
        # Use the same champion names as make_5_assignments: Aatrox, LeeSin, Viktor, Jinx, Thresh
        champs_s = [
            make_champ("Aatrox", damage_type="AD", role_tags=["TANK"], waveclear=3, teamfight=3, meta_tier={"TOP": "S"}),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], waveclear=3, teamfight=3, meta_tier={"JG": "S"}),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], waveclear=3, teamfight=3, meta_tier={"MID": "S"}),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], waveclear=3, teamfight=3, meta_tier={"ADC": "S"}),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"], waveclear=3, teamfight=3, meta_tier={"SUP": "S"}),
        ]
        champs_d = [
            make_champ("Aatrox", damage_type="AD", role_tags=["TANK"], waveclear=3, teamfight=3, meta_tier={"TOP": "D"}),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], waveclear=3, teamfight=3, meta_tier={"JG": "D"}),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], waveclear=3, teamfight=3, meta_tier={"MID": "D"}),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], waveclear=3, teamfight=3, meta_tier={"ADC": "D"}),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT"], waveclear=3, teamfight=3, meta_tier={"SUP": "D"}),
        ]
        assignments = make_5_assignments()
        map_s = {c.champion_name: c for c in champs_s}
        map_d = {c.champion_name: c for c in champs_d}

        score_s = comp_optimizer.calculate_score(assignments, champs_s, map_s)
        score_d = comp_optimizer.calculate_score(assignments, champs_d, map_d)

        # S=100, D=20, diff=80. Weight=0.10, so 8 points difference
        assert score_s > score_d
        assert (score_s - score_d) == pytest.approx(8.0, abs=2)


class TestChampionRolesGuide:
    def test_champion_roles_guide_generated(self, comp_optimizer: CompOptimizerService) -> None:
        """Champion roles guide should be generated for each assignment."""
        # Use champion names matching make_5_assignments: Aatrox, LeeSin, Viktor, Jinx, Thresh
        champs = [
            make_champ("Aatrox", damage_type="AD", role_tags=["TANK"], engage=5, teamfight=5, waveclear=4,
                        champion_name_ko="아트록스", play_tips="Q 3단 스윗스팟."),
            make_champ("LeeSin", damage_type="AD", role_tags=["BRUISER"], engage=4, teamfight=3, waveclear=3,
                        champion_name_ko="리 신", play_tips="인섹 콤보가 핵심."),
            make_champ("Viktor", damage_type="AP", role_tags=["MAGE"], engage=3, teamfight=4, waveclear=5,
                        champion_name_ko="빅토르", play_tips="헥스코어 진화."),
            make_champ("Jinx", damage_type="AD", role_tags=["MARKSMAN"], engage=1, teamfight=4, waveclear=3,
                        champion_name_ko="징크스", play_tips="로켓/미니건 전환."),
            make_champ("Thresh", damage_type="AP", role_tags=["SUPPORT", "TANK"], engage=4, peel=4, teamfight=3, waveclear=1,
                        champion_name_ko="쓰레쉬", play_tips="Q 적중 판단."),
        ]
        # engage = 5+4+3+1+4 = 17 >= 15 → 이니시 comp
        assignments = make_5_assignments()
        champion_attrs_map = {c.champion_name: c for c in champs}
        analysis = comp_optimizer.analyze(assignments, champs, champion_attrs_map)

        # Should contain 챔피언별 역할 section
        assert "챔피언별 역할" in analysis.strategy_guide
        # Should contain Korean champion names
        assert "아트록스" in analysis.strategy_guide
        assert "리 신" in analysis.strategy_guide
        assert "징크스" in analysis.strategy_guide
        # Should contain play tips
        assert "팁:" in analysis.strategy_guide

    def test_champion_roles_tank_in_engage_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """TANK in engage comp should get engage role description."""
        comp_types = ["이니시"]
        attrs = make_champ("Ornn", role_tags=["TANK"])
        assignment = make_assignment(lane="TOP", champion_name="Ornn")
        role = comp_optimizer._get_champion_comp_role(assignment, attrs, comp_types)
        assert "이니시" in role

    def test_champion_roles_marksman_in_protect_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """MARKSMAN in protect comp should be told to stay safe."""
        comp_types = ["프로텍트"]
        attrs = make_champ("Jinx", role_tags=["MARKSMAN"])
        assignment = make_assignment(lane="ADC", champion_name="Jinx")
        role = comp_optimizer._get_champion_comp_role(assignment, attrs, comp_types)
        assert "딜러" in role or "딜링" in role

    def test_champion_roles_assassin_in_pick_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """ASSASSIN in pick comp should be told to catch isolated targets."""
        comp_types = ["픽"]
        attrs = make_champ("Zed", role_tags=["ASSASSIN"])
        assignment = make_assignment(lane="MID", champion_name="Zed")
        role = comp_optimizer._get_champion_comp_role(assignment, attrs, comp_types)
        assert "캐치" in role or "고립" in role

    def test_champion_roles_bruiser_in_split_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """BRUISER with high splitpush in split comp should get split role."""
        comp_types = ["스플릿"]
        attrs = make_champ("Fiora", role_tags=["BRUISER"], splitpush=5)
        assignment = make_assignment(lane="TOP", champion_name="Fiora")
        role = comp_optimizer._get_champion_comp_role(assignment, attrs, comp_types)
        assert "스플릿" in role

    def test_champion_roles_mage_in_poke_comp(self, comp_optimizer: CompOptimizerService) -> None:
        """MAGE with high poke in poke comp should get poke role."""
        comp_types = ["포킹"]
        attrs = make_champ("Xerath", role_tags=["MAGE"], poke=5)
        assignment = make_assignment(lane="MID", champion_name="Xerath")
        role = comp_optimizer._get_champion_comp_role(assignment, attrs, comp_types)
        assert "포킹" in role
