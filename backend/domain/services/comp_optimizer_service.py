from itertools import product
from domain.models.player import Player, ChampionStats
from domain.models.champion import ChampionAttributes
from domain.models.composition import (
    Assignment,
    TeamAnalysis,
    LaneAssignment,
    Composition,
)


# Score weights (out of 100 total)
WEIGHT_PERSONAL_MASTERY: float = 0.30
WEIGHT_AD_AP_BALANCE: float = 0.20
WEIGHT_FRONTLINE: float = 0.15
WEIGHT_DEAL_COMPOSITION: float = 0.15
WEIGHT_WAVECLEAR: float = 0.10
WEIGHT_SPLITPUSH: float = 0.10

# Penalties
PENALTY_FULL_AD: int = -30
PENALTY_FULL_AP: int = -30
PENALTY_NO_FRONTLINE: int = -25
PENALTY_LOW_WAVECLEAR: int = -10
PENALTY_OFF_LANE_PER_CHAMPION: int = -15  # 챔피언이 primary_lanes 밖 라인에 배정될 때

# Max values for normalization
MAX_WAVECLEAR: int = 25  # 5 champions * 5 max each
MAX_SPLITPUSH: int = 25
MAX_TEAMFIGHT: int = 25

# How many top champions per player to consider
TOP_CHAMPIONS_PER_PLAYER: int = 10


class CompOptimizerService:
    """Champion composition optimization service.

    Scores compositions based on:
    - Personal mastery (30%)
    - AD/AP balance (20%)
    - Frontline presence (15%)
    - Deal composition / teamfight (15%)
    - Waveclear (10%)
    - Splitpush (10%)

    No external dependencies -- uses only domain models.
    """

    def _get_player_champion_pool(
        self,
        player: Player,
        champion_attrs_map: dict[str, ChampionAttributes],
        max_champions: int = TOP_CHAMPIONS_PER_PLAYER,
    ) -> list[ChampionStats]:
        """Get a player's top champions. No hard filtering — scoring handles priority."""
        pool: list[ChampionStats] = []
        for champ in player.top_champions:
            if len(pool) >= max_champions:
                break
            pool.append(champ)
        return pool if pool else [ChampionStats(champion_name="Unknown", games=0)]

    def _mastery_bonus(self, mastery_points: int) -> float:
        """Mastery points bonus: 10만+ → 0.3, 5만+ → 0.2, 1만+ → 0.1, 미만 → 0.0"""
        if mastery_points >= 100_000:
            return 0.3
        elif mastery_points >= 50_000:
            return 0.2
        elif mastery_points >= 10_000:
            return 0.1
        return 0.0

    def _personal_mastery_score(
        self, assignments: list[Assignment]
    ) -> float:
        """Calculate personal mastery score (0-100 scale).

        score = (win_rate * game_count_factor) + mastery_bonus
        - game_count_factor: games/10 (max 1.0), 0게임이면 0.1
        - mastery_bonus: 10만+점 → 0.3, 5만+ → 0.2, 1만+ → 0.1
        - 최대 1.3 (승률1.0 * 게임팩터1.0 + 숙련도0.3)
        """
        if not assignments:
            return 0.0

        total = 0.0
        for a in assignments:
            game_factor = min(a.personal_games / 10.0, 1.0) if a.personal_games > 0 else 0.1
            base = a.personal_win_rate * game_factor
            bonus = self._mastery_bonus(a.mastery_points)
            total += base + bonus
        avg = total / len(assignments)
        # Normalize: max possible is 1.3 (1.0 + 0.3)
        return min(avg / 1.3, 1.0) * 100.0

    def _ad_ap_balance_score(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> float:
        """Calculate AD/AP balance score (0-100 scale).

        Best: 2 AD + 3 AP or 3 AD + 2 AP.
        Penalized for extreme imbalance.
        """
        if not champion_attrs_list:
            return 0.0

        ad_count = sum(1 for a in champion_attrs_list if a.damage_type == "AD")
        ap_count = sum(1 for a in champion_attrs_list if a.damage_type == "AP")
        hybrid_count = sum(1 for a in champion_attrs_list if a.damage_type == "HYBRID")

        total = len(champion_attrs_list)
        if total == 0:
            return 0.0

        # Hybrid counts as 0.5 AD + 0.5 AP
        effective_ad = ad_count + hybrid_count * 0.5
        effective_ap = ap_count + hybrid_count * 0.5

        if total > 0:
            ad_ratio = effective_ad / total
            ap_ratio = effective_ap / total
        else:
            ad_ratio = 0.5
            ap_ratio = 0.5

        # Ideal ratio is 0.4-0.6 for each side
        # Perfect score when ratio is between 0.4 and 0.6
        balance = 1.0 - abs(ad_ratio - 0.5) * 2.0  # 1.0 at 50/50, 0.0 at 100/0
        balance = max(balance, 0.0)

        return balance * 100.0

    def _frontline_score(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> float:
        """Calculate frontline score (0-100 scale).

        100 if at least one TANK or BRUISER, 0 otherwise.
        """
        has_frontline = any(
            "TANK" in a.role_tags or "BRUISER" in a.role_tags
            for a in champion_attrs_list
        )
        return 100.0 if has_frontline else 0.0

    def _deal_composition_score(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> float:
        """Calculate deal composition score based on total teamfight (0-100 scale)."""
        if not champion_attrs_list:
            return 0.0
        total_teamfight = sum(a.teamfight for a in champion_attrs_list)
        return min(total_teamfight / MAX_TEAMFIGHT, 1.0) * 100.0

    def _waveclear_score_value(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> int:
        """Get total waveclear score."""
        return sum(a.waveclear for a in champion_attrs_list)

    def _waveclear_score(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> float:
        """Calculate waveclear score (0-100 scale)."""
        total = self._waveclear_score_value(champion_attrs_list)
        return min(total / MAX_WAVECLEAR, 1.0) * 100.0

    def _splitpush_score(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> float:
        """Calculate splitpush score (0-100 scale)."""
        if not champion_attrs_list:
            return 0.0
        total = sum(a.splitpush for a in champion_attrs_list)
        return min(total / MAX_SPLITPUSH, 1.0) * 100.0

    def _calculate_penalties(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> dict[str, int]:
        """Calculate penalty deductions."""
        penalties: dict[str, int] = {}

        ad_count = sum(
            1
            for a in champion_attrs_list
            if a.damage_type in ("AD", "HYBRID")
        )
        ap_count = sum(
            1
            for a in champion_attrs_list
            if a.damage_type in ("AP", "HYBRID")
        )

        # Full AD (0 AP): -30
        if ap_count == 0 and len(champion_attrs_list) > 0:
            penalties["full_ad"] = PENALTY_FULL_AD

        # Full AP (0 AD): -30
        if ad_count == 0 and len(champion_attrs_list) > 0:
            penalties["full_ap"] = PENALTY_FULL_AP

        # No frontline: -25
        has_frontline = any(
            "TANK" in a.role_tags or "BRUISER" in a.role_tags
            for a in champion_attrs_list
        )
        if not has_frontline and len(champion_attrs_list) > 0:
            penalties["no_frontline"] = PENALTY_NO_FRONTLINE

        # Low waveclear: -10
        total_waveclear = self._waveclear_score_value(champion_attrs_list)
        if total_waveclear < 10 and len(champion_attrs_list) > 0:
            penalties["low_waveclear"] = PENALTY_LOW_WAVECLEAR

        return penalties

    def calculate_score(
        self,
        assignments: list[Assignment],
        champion_attrs_list: list[ChampionAttributes],
    ) -> float:
        """Calculate total composition score (0-100 minus penalties).

        Weights:
        - Personal mastery: 30%
        - AD/AP balance: 20%
        - Frontline: 15%
        - Deal composition: 15%
        - Waveclear: 10%
        - Splitpush: 10%
        """
        personal = self._personal_mastery_score(assignments)

        # 4명 이하: 팀 조합 평가 불가 → 개인 숙련도 위주
        if len(assignments) < 4:
            return personal

        ad_ap = self._ad_ap_balance_score(champion_attrs_list)
        frontline = self._frontline_score(champion_attrs_list)
        deal = self._deal_composition_score(champion_attrs_list)
        waveclear = self._waveclear_score(champion_attrs_list)
        splitpush = self._splitpush_score(champion_attrs_list)

        base_score = (
            personal * WEIGHT_PERSONAL_MASTERY
            + ad_ap * WEIGHT_AD_AP_BALANCE
            + frontline * WEIGHT_FRONTLINE
            + deal * WEIGHT_DEAL_COMPOSITION
            + waveclear * WEIGHT_WAVECLEAR
            + splitpush * WEIGHT_SPLITPUSH
        )

        penalties = self._calculate_penalties(champion_attrs_list)
        penalty_total = sum(penalties.values())

        return max(base_score + penalty_total, 0.0)

    def analyze(
        self,
        assignments: list[Assignment],
        champion_attrs_list: list[ChampionAttributes],
    ) -> TeamAnalysis:
        """Analyze a team composition and return detailed analysis."""
        if not champion_attrs_list:
            return TeamAnalysis()

        total = len(champion_attrs_list)
        is_partial = total < 4  # 2~3명: 팀 조합 평가 불가

        ad_count = sum(1 for a in champion_attrs_list if a.damage_type == "AD")
        ap_count = sum(1 for a in champion_attrs_list if a.damage_type == "AP")
        hybrid_count = sum(1 for a in champion_attrs_list if a.damage_type == "HYBRID")

        effective_ad = ad_count + hybrid_count * 0.5
        effective_ap = ap_count + hybrid_count * 0.5

        ad_ratio = effective_ad / total if total > 0 else 0.0
        ap_ratio = effective_ap / total if total > 0 else 0.0

        has_frontline = any(
            "TANK" in a.role_tags or "BRUISER" in a.role_tags
            for a in champion_attrs_list
        )

        waveclear_total = sum(a.waveclear for a in champion_attrs_list)
        splitpush_total = sum(a.splitpush for a in champion_attrs_list)
        teamfight_total = sum(a.teamfight for a in champion_attrs_list)

        # Build per-champion stat contributions
        stat_keys = ["teamfight", "engage", "poke", "pick", "burst", "waveclear", "splitpush", "peel"]
        stat_contributions: dict[str, list[dict]] = {}
        for key in stat_keys:
            contribs = []
            for attrs in champion_attrs_list:
                val = getattr(attrs, key, 0)
                if val > 0:
                    contribs.append({"champion": attrs.champion_name, "value": val})
            # Sort by value descending
            contribs.sort(key=lambda x: x["value"], reverse=True)
            stat_contributions[key] = contribs

        # 2~3명일 때는 페널티 없음
        penalties = {} if is_partial else self._calculate_penalties(champion_attrs_list)

        # Determine strengths and weaknesses
        strengths: list[str] = []
        weaknesses: list[str] = []

        if 0.35 <= ad_ratio <= 0.65:
            strengths.append("균형 잡힌 AD/AP 비율")
        if has_frontline:
            strengths.append("안정적인 프론트라인")
        if waveclear_total >= 15:
            strengths.append("우수한 웨이브클리어")
        if splitpush_total >= 15:
            strengths.append("강력한 스플릿 옵션")
        if teamfight_total >= 18:
            strengths.append("강력한 팀파이트")

        engage_total = sum(a.engage for a in champion_attrs_list)
        peel_total = sum(a.peel for a in champion_attrs_list)
        poke_total = sum(a.poke for a in champion_attrs_list)
        pick_total = sum(a.pick for a in champion_attrs_list)
        burst_total = sum(a.burst for a in champion_attrs_list)

        if engage_total >= 15:
            strengths.append("뛰어난 이니시에이트")
        if peel_total >= 12:
            strengths.append("강력한 필링")
        if poke_total >= 14:
            strengths.append("강력한 포킹")
        if pick_total >= 14:
            strengths.append("뛰어난 캐치 능력")
        if burst_total >= 16:
            strengths.append("높은 순간 폭딜")

        if "full_ad" in penalties:
            weaknesses.append("풀 AD 조합 - AP 딜러 부재")
        if "full_ap" in penalties:
            weaknesses.append("풀 AP 조합 - AD 딜러 부재")
        if "no_frontline" in penalties:
            weaknesses.append("프론트라인 부재")
        if "low_waveclear" in penalties:
            weaknesses.append("웨이브클리어 부족")
        if engage_total < 8:
            weaknesses.append("이니시에이트 부족")
        if teamfight_total < 12:
            weaknesses.append("팀파이트 능력 부족")
        if poke_total < 6:
            weaknesses.append("포킹 능력 부족")

        # Detect composition archetype(s) — 4명 이하면 조합 유형 판별 스킵
        comp_types: list[str] = []
        strategy_parts: list[str] = []

        if is_partial:
            comp_type = ""
            strategy_guide = "인원이 부족하여 조합 유형 판별이 불가합니다. 개인 숙련도 기준으로 추천합니다."
            return TeamAnalysis(
                ad_ratio=round(ad_ratio, 2),
                ap_ratio=round(ap_ratio, 2),
                has_frontline=has_frontline,
                waveclear_score=waveclear_total,
                splitpush_score=splitpush_total,
                teamfight_score=teamfight_total,
                engage_score=engage_total,
                peel_score=peel_total,
                poke_score=poke_total,
                pick_score=pick_total,
                burst_score=burst_total,
                comp_type=comp_type,
                strategy_guide=strategy_guide,
                strengths=strengths,
                weaknesses=weaknesses,
                penalties=penalties,
                stat_contributions=stat_contributions,
            )

        strategy_map = {
            "이니시": "이니시에이터가 싸움을 걸어 한타를 유도하세요. 오브젝트(드래곤/바론) 타이밍에 적극적으로 싸움을 걸고, 이니시 타이밍을 팀원과 맞추는 것이 핵심입니다.",
            "포킹": "오브젝트 앞에서 스킬로 적의 체력을 깎은 뒤 진입하세요. 정면 한타는 피하고, 적이 체력 불리한 상태에서 싸우는 것이 이상적입니다.",
            "픽": "시야를 장악하고 고립된 적을 잡으세요. 소규모 교전에서 숫자 우위를 만들고, 잡은 뒤 바로 오브젝트로 전환하세요.",
            "스플릿": "1-3-1 또는 1-4 라인 운영으로 사이드를 압박하세요. 스플릿푸셔가 압박하는 동안 나머지는 오브젝트 근처에서 시간을 끄세요.",
            "한타": "5:5 정면 한타에서 강합니다. 좁은 지형(드래곤 핏, 바론 핏)을 활용하고, 궁극기 쿨타임에 맞춰 싸우세요.",
            "프로텍트": "원딜(캐리)를 중심으로 포지셔닝하세요. 서포터와 탱커가 원딜을 보호하며, 원딜이 안전하게 딜을 넣는 것이 최우선입니다.",
            "폭딜": "핵심 타겟(원딜/미드)을 빠르게 제거하세요. 교전이 길어지면 불리하니 빠르게 킬을 따고 전투를 끝내세요.",
        }

        if engage_total >= 15:
            comp_types.append("이니시")
            strategy_parts.append(strategy_map["이니시"])
        if poke_total >= 14:
            comp_types.append("포킹")
            strategy_parts.append(strategy_map["포킹"])
        if pick_total >= 14:
            comp_types.append("픽")
            strategy_parts.append(strategy_map["픽"])
        if splitpush_total >= 14 and any(a.splitpush >= 4 for a in champion_attrs_list):
            comp_types.append("스플릿")
            strategy_parts.append(strategy_map["스플릿"])
        if teamfight_total >= 18:
            comp_types.append("한타")
            strategy_parts.append(strategy_map["한타"])
        if peel_total >= 12 and any("MARKSMAN" in a.role_tags for a in champion_attrs_list):
            comp_types.append("프로텍트")
            strategy_parts.append(strategy_map["프로텍트"])
        if burst_total >= 16:
            comp_types.append("폭딜")
            strategy_parts.append(strategy_map["폭딜"])

        if comp_types:
            comp_type = " + ".join(t + " 조합" for t in comp_types)
        else:
            comp_type = "균형 조합"

        strategy_guide = "\n".join(strategy_parts) if strategy_parts else ""

        return TeamAnalysis(
            ad_ratio=round(ad_ratio, 2),
            ap_ratio=round(ap_ratio, 2),
            has_frontline=has_frontline,
            waveclear_score=waveclear_total,
            splitpush_score=splitpush_total,
            teamfight_score=teamfight_total,
            engage_score=engage_total,
            peel_score=peel_total,
            poke_score=poke_total,
            pick_score=pick_total,
            burst_score=burst_total,
            comp_type=comp_type,
            strategy_guide=strategy_guide,
            strengths=strengths,
            weaknesses=weaknesses,
            penalties=penalties,
        )

    def _count_off_lane_champions(
        self,
        assignments: list[Assignment],
        champion_attrs_map: dict[str, ChampionAttributes],
    ) -> int:
        """Count how many champions are playing outside their primary_lanes."""
        count = 0
        for a in assignments:
            attrs = champion_attrs_map.get(a.champion_name)
            if attrs and attrs.primary_lanes and a.lane not in attrs.primary_lanes:
                count += 1
        return count

    def optimize(
        self,
        players: list[Player],
        lane_assignments: list[LaneAssignment],
        champion_attrs_map: dict[str, ChampionAttributes],
        top_n: int = 5,
    ) -> list[Composition]:
        """Find optimal champion compositions for the given lane assignments.

        For each lane assignment:
        1. Get each player's top 5 champions
        2. Generate all combinations (max 5^5 = 3125)
        3. Score each combination (including off-lane penalty)
        4. Return top_n overall compositions
        """
        player_map: dict[str, Player] = {}
        for p in players:
            key = f"{p.game_name}#{p.tag_line}"
            player_map[key] = p

        all_compositions: list[Composition] = []

        for lane_assignment in lane_assignments:
            # Build champion pools for each assignment slot
            champion_pools: list[list[ChampionStats]] = []

            for assignment in lane_assignment.assignments:
                key = f"{assignment.player_game_name}#{assignment.player_tag_line}"
                player = player_map.get(key)
                if player is None:
                    champion_pools.append(
                        [ChampionStats(champion_name="Unknown", games=0)]
                    )
                    continue

                pool = self._get_player_champion_pool(
                    player, champion_attrs_map
                )

                # Filter: prefer champions that can play this lane
                lane = assignment.lane
                lane_fit: list[ChampionStats] = []
                lane_unfit: list[ChampionStats] = []
                for champ in pool:
                    attrs = champion_attrs_map.get(champ.champion_name)
                    if attrs and attrs.primary_lanes and lane not in attrs.primary_lanes:
                        lane_unfit.append(champ)
                    else:
                        lane_fit.append(champ)

                # primary_lanes에 맞는 챔피언 우선, 없으면 전체 풀 사용 (빈 결과 방지)
                if lane_fit:
                    champion_pools.append(lane_fit[:5])
                elif lane_unfit:
                    # 라인에 맞는 챔피언이 없지만 다른 챔피언은 있음 → fallback
                    champion_pools.append(lane_unfit[:3])
                else:
                    # 챔피언이 아예 없음 → 이 라인 배정 스킵
                    champion_pools = None
                    break

            if champion_pools is None:
                continue  # 다음 라인 배정으로

            # Generate all combinations of champion picks
            for combo in product(*champion_pools):
                assignments: list[Assignment] = []
                attrs_list: list[ChampionAttributes] = []

                for i, champ_stats in enumerate(combo):
                    base_assignment = lane_assignment.assignments[i]
                    attrs = champion_attrs_map.get(champ_stats.champion_name)
                    if attrs is None:
                        attrs = ChampionAttributes(
                            champion_name=champ_stats.champion_name,
                            champion_id=champ_stats.champion_id,
                        )

                    assignments.append(
                        Assignment(
                            player_game_name=base_assignment.player_game_name,
                            player_tag_line=base_assignment.player_tag_line,
                            lane=base_assignment.lane,
                            champion_name=champ_stats.champion_name,
                            champion_id=champ_stats.champion_id
                            or attrs.champion_id,
                            personal_win_rate=champ_stats.win_rate,
                            personal_kda=champ_stats.kda,
                            personal_games=champ_stats.games,
                            mastery_points=champ_stats.mastery_points,
                        )
                    )
                    attrs_list.append(attrs)

                # Check for duplicate champions in the same composition
                champ_names = [a.champion_name for a in assignments]
                if len(set(champ_names)) < len(champ_names):
                    continue  # Skip compositions with duplicate champions

                score = self.calculate_score(assignments, attrs_list)

                # Off-lane penalty: 챔피언이 primary_lanes 밖에서 플레이 시 감점
                off_lane_count = self._count_off_lane_champions(
                    assignments, champion_attrs_map
                )
                score += off_lane_count * PENALTY_OFF_LANE_PER_CHAMPION

                # Lane assignment quality bonus: 라인 배정 적합도 반영 (0~10점)
                # lane_assignment.score = sum of (win_rate * game_count_weight) per player
                # Normalize: max possible ~ 1.0 per player * 5 players = 5.0
                max_lane_score = len(assignments) * 1.0
                if max_lane_score > 0:
                    lane_quality = (lane_assignment.score / max_lane_score) * 10.0
                    score += lane_quality

                score = max(score, 0.0)
                analysis = self.analyze(assignments, attrs_list)

                all_compositions.append(
                    Composition(
                        total_score=round(score, 1),
                        assignments=assignments,
                        team_analysis=analysis,
                    )
                )

        # Sort by total_score descending
        all_compositions.sort(key=lambda c: c.total_score, reverse=True)

        # Assign ranks and return top_n
        result = all_compositions[:top_n]
        for i, comp in enumerate(result):
            comp.rank = i + 1

        return result
