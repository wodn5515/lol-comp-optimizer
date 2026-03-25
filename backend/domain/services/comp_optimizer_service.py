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
WEIGHT_PERSONAL_MASTERY: float = 0.25
WEIGHT_META_TIER: float = 0.10
WEIGHT_AD_AP_BALANCE: float = 0.15
WEIGHT_FRONTLINE: float = 0.15
WEIGHT_DEAL_COMPOSITION: float = 0.15
WEIGHT_WAVECLEAR: float = 0.10
WEIGHT_SPLITPUSH: float = 0.10

# Meta tier score mapping
META_TIER_SCORES: dict[str, int] = {"S": 100, "A": 80, "B": 60, "C": 40, "D": 20}

# Penalties (점수에서 직접 감점)
PENALTY_FULL_AD: int = -30
PENALTY_FULL_AP: int = -30
PENALTY_NO_FRONTLINE: int = -25
PENALTY_LOW_WAVECLEAR: int = -10
PENALTY_OFF_LANE_PER_CHAMPION: int = -25
PENALTY_LOW_ENGAGE: int = -10     # 이니시 부족
PENALTY_LOW_PEEL: int = -8        # 필링 부족
PENALTY_LOW_TEAMFIGHT: int = -8   # 팀파이트 부족

# Max values for normalization
MAX_WAVECLEAR: int = 25  # 5 champions * 5 max each
MAX_SPLITPUSH: int = 25
MAX_TEAMFIGHT: int = 25

# How many top champions per player to consider (no artificial limit)
TOP_CHAMPIONS_PER_PLAYER: int = 50

# Comp types that REQUIRE frontline — penalty applies if no frontline
FRONTLINE_REQUIRED_COMP_TYPES = {"이니시", "한타", "프로텍트"}

# Comp types that do NOT need frontline — no penalty regardless
FRONTLINE_NOT_NEEDED_COMP_TYPES = {"포킹", "픽", "폭딜", "다이브"}

# Synergy strategies for comp type pairs
SYNERGY_STRATEGIES: dict[frozenset, str] = {
    frozenset(["스플릿", "글로벌"]): "스플릿러가 사이드 압박 중 글로벌 궁으로 즉시 합류 가능. 쉔 R이나 TF R로 순간 숫자 우위를 만드세요.",
    frozenset(["포킹", "디스인게이지"]): "포킹으로 적 체력을 깎다가 적이 진입하면 디스인게이지로 끊고 다시 포킹. 이 사이클을 반복하세요.",
    frozenset(["이니시", "궁합"]): "이니시 타이밍에 AoE 궁극기를 연쇄하세요. 좁은 지형(드래곤 핏, 바론 핏)에서 싸우면 효과 극대화.",
    frozenset(["이니시", "한타"]): "탱커가 이니시와 프론트라인을 겸임. 정면 5v5에서 CC 체인 후 원딜이 안전하게 딜링하세요.",
    frozenset(["픽", "다이브"]): "시야로 적 위치를 파악하고 고립된 적에게 다이브. 녹턴 R 등으로 순간 접근 후 폭딜로 삭제하세요.",
    frozenset(["스플릿", "픽"]): "스플릿으로 적을 분산시킨 후 이동 중인 적을 캐치. 소규모 교전에서 숫자 우위를 만드세요.",
    frozenset(["프로텍트", "디스인게이지"]): "원딜 보호에 올인. 적의 돌진을 전부 끊고 원딜이 안전하게 딜을 넣는 것이 최우선입니다.",
    frozenset(["다이브", "폭딜"]): "전원 백라인 직행. 다이버가 CC로 잡으면 어쌔신이 원샷. 교전을 2~3초 내에 끝내세요.",
}

# Detailed strategy for each comp type
COMP_STRATEGIES: dict[str, dict[str, str]] = {
    "이니시": {
        "guide": "이니시에이터가 싸움을 걸어 한타를 유도하세요. 오브젝트(드래곤/바론) 타이밍에 적극적으로 싸움을 걸고, CC를 연쇄적으로 사용하세요.",
        "win_condition": "오브젝트 앞에서 5v5 한타를 강제하고 CC 체인으로 핵심 타겟을 집중 공격하세요.",
        "caution": "궁극기 쿨타임에는 싸움을 피하세요. 뒤처진 상태에서의 이니시는 자살행위입니다.",
    },
    "디스인게이지": {
        "guide": "상대의 이니시를 끊고 반격하는 리액션 플레이를 하세요. 잔나 R, 그라가스 R 등으로 적의 돌진을 무력화하세요.",
        "win_condition": "상대 이니시를 무력화한 뒤 쿨타임이 빠진 적을 역습하세요.",
        "caution": "우리 팀이 먼저 싸움을 걸 수 없습니다. 항상 상대의 액션에 반응하세요. 시야 확보가 핵심입니다.",
    },
    "포킹": {
        "guide": "오브젝트 앞에서 30~60초간 원거리 스킬로 적 체력을 깎으세요. 적이 50% 이하가 되면 진입하거나 오브젝트를 가져가세요.",
        "win_condition": "정면 한타를 피하고 포킹으로 체력 차이를 만든 뒤 싸우세요. 시즈(타워 밀기)도 효과적입니다.",
        "caution": "정면 한타는 절대 금지. 스킬을 빗나가면 안 됩니다. 디스인게이지 수단을 항상 남겨두세요.",
    },
    "픽": {
        "guide": "시야를 장악하고 고립된 적을 잡으세요. 적 정글 입구, 오브젝트 이동 경로에 매복하세요.",
        "win_condition": "한 명을 잡고 바로 오브젝트(드래곤/바론/타워)로 전환하세요. 5v5는 피하세요.",
        "caution": "실패한 캐치에 깊이 쫓아가지 마세요. 적이 뭉쳐 다니면 캐치가 어려워지므로 스플릿으로 분산을 유도하세요.",
    },
    "스플릿": {
        "guide": "1-3-1 또는 1-4로 사이드를 압박하세요. 스플릿푸셔가 사이드를 밀 때 나머지는 오브젝트 근처에서 시간을 끄세요.",
        "win_condition": "적이 스플릿러에게 1명 보내면 1v1으로 이기고, 2명 보내면 나머지가 4v3으로 오브젝트를 가져가세요.",
        "caution": "스플릿러는 시야 없이 깊이 들어가지 마세요. 나머지 4인은 절대 싸움을 걸지 말고 시간만 끄세요.",
    },
    "한타": {
        "guide": "5v5 정면 한타에서 승부하세요. 탱커가 앞에서 적 스킬을 흡수하고 원딜이 뒤에서 안전하게 딜링하세요.",
        "win_condition": "좁은 지형(드래곤 핏, 바론 핏)에서 한타를 유도하고 궁극기 쿨타임에 맞춰 싸우세요.",
        "caution": "원딜이 앞으로 나가면 안 됩니다. 탱커가 너무 깊이 들어가서 원딜과 떨어지지 마세요.",
    },
    "프로텍트": {
        "guide": "하이퍼캐리(원딜)를 중심으로 포지셔닝하세요. 서포터와 탱커는 원딜 옆에서 보호하세요.",
        "win_condition": "원딜이 3코어 이상 완성되면 그룹하여 한타. 원딜이 살아있으면 한타에서 이깁니다.",
        "caution": "초반에는 약하니 싸움을 피하고 파밍하세요. 원딜이 죽으면 한타는 자동 패배입니다.",
    },
    "다이브": {
        "guide": "프론트라인을 무시하고 적 백라인(원딜/미드)에 직행하세요. 안개 속에서 플랭크로 접근하세요.",
        "win_condition": "적 핵심 딜러를 2초 안에 삭제하세요. 딜러가 죽으면 나머지 탱커만으로는 이길 수 없습니다.",
        "caution": "궁극기 없이 다이브하지 마세요. 뒤처진 상태에서는 다이브해도 못 죽입니다. 30분 전에 끝내세요.",
    },
    "스커미시": {
        "guide": "초반 2v2, 3v3 싸움을 적극적으로 하세요. 정글 침입, 스커틀 싸움, 갱킹을 쉬지 않고 하세요.",
        "win_condition": "25분 안에 게임을 끝내세요. 모든 초반 싸움에서 이겨 골드 차이를 벌리세요.",
        "caution": "후반으로 갈수록 약해집니다. 이긴 싸움 후 반드시 오브젝트로 전환하세요. 시간 끌지 마세요.",
    },
    "궁합": {
        "guide": "AoE 궁극기를 연쇄로 사용하세요. 좁은 지형에서 적이 뭉쳤을 때 한 번에 터뜨리세요.",
        "win_condition": "3명 이상에게 풀콤보를 적중시키면 한타 즉시 승리. 드래곤 핏, 바론 핏에서 싸우세요.",
        "caution": "궁극기가 없으면 절대 싸우지 마세요. 적이 분산하면 콤보 효율이 떨어지므로 좁은 지형을 유도하세요.",
    },
    "폭딜": {
        "guide": "적의 핵심 타겟(원딜/미드)을 빠르게 제거하세요. 안개 속 매복과 플랭크가 핵심입니다.",
        "win_condition": "교전을 2~3초 안에 끝내세요. 교전이 길어지면 불리합니다.",
        "caution": "탱커를 때리지 마세요 (못 죽입니다). 존야/GA를 산 적에게는 쿨타임을 기다려야 합니다. 후반에 약해집니다.",
    },
}


class CompOptimizerService:
    """Champion composition optimization service.

    Scores compositions based on:
    - Personal mastery (25%)
    - Meta tier (10%)
    - AD/AP balance (15%)
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
        else:
            ad_ratio = 0.5

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

    def _meta_tier_score(
        self,
        assignments: list[Assignment],
        champion_attrs_map: dict[str, ChampionAttributes],
    ) -> float:
        """Average meta tier score for each champion in their assigned lane.

        Uses META_TIER_SCORES mapping: S=100, A=80, B=60, C=40, D=20.
        Defaults to B (60) if meta_tier data is missing.
        """
        if not assignments:
            return 0.0
        total = 0.0
        for a in assignments:
            attrs = champion_attrs_map.get(a.champion_name)
            if attrs and attrs.meta_tier:
                tier = attrs.meta_tier.get(a.lane, "B")
                total += META_TIER_SCORES.get(tier, 60)
            else:
                total += 60  # default B tier
        return total / len(assignments)

    def _get_champion_comp_role(
        self,
        assignment: Assignment,
        attrs: ChampionAttributes | None,
        comp_types: list[str],
    ) -> str:
        """Determine a champion's role description based on their tags and the comp type."""
        if attrs is None:
            return "팀 내 역할을 수행하세요."

        role_tags = set(attrs.role_tags)
        comp_set = set(comp_types)

        # TANK in engage/teamfight comp
        if "TANK" in role_tags:
            if "이니시" in comp_set:
                return "이니시 담당. 궁으로 싸움을 걸고 팀이 따라오면 승리."
            if "한타" in comp_set:
                return "프론트라인. 앞에서 적 스킬 흡수하고 원딜과 너무 떨어지지 마세요."
            if "프로텍트" in comp_set:
                return "원딜 보호 담당. 적 다이버/어쌔신 차단이 최우선."
            if "디스인게이지" in comp_set:
                return "디스인게이지 담당. 적의 돌진을 CC로 끊고 아군을 보호하세요."
            return "프론트라인. 적 CC와 딜을 흡수하며 아군이 안전하게 딜할 공간을 만드세요."

        # MARKSMAN
        if "MARKSMAN" in role_tags:
            if "프로텍트" in comp_set:
                return "메인 딜러. 프론트 뒤에서 안전하게 딜링. 절대 앞으로 나가지 마세요."
            if "한타" in comp_set:
                return "후방 딜러. 탱커 뒤에서 안전하게 딜링. 포지셔닝이 생명입니다."
            if "포킹" in comp_set:
                return "지속 딜러. 안전 거리에서 딜링하며 적이 접근하면 후퇴하세요."
            return "팀의 핵심 딜러. 생존하면서 지속적으로 딜을 넣는 것이 최우선입니다."

        # ASSASSIN
        if "ASSASSIN" in role_tags:
            if "픽" in comp_set:
                return "캐치 후 폭딜 담당. 시야 확보된 곳에서 고립된 적을 노리세요."
            if "다이브" in comp_set:
                return "백라인 다이브 담당. 적 원딜/미드를 빠르게 삭제하세요."
            if "폭딜" in comp_set:
                return "암살 담당. 적 핵심 타겟을 2초 안에 처치하세요. 교전이 길어지면 불리합니다."
            if "스커미시" in comp_set:
                return "초반 스커미시 주도. 정글 침입과 소규모 교전에서 킬을 따내세요."
            return "적 핵심 딜러 암살 담당. 싸움 시작 후 적 후방으로 우회 진입하세요."

        # BRUISER
        if "BRUISER" in role_tags:
            if "스플릿" in comp_set and attrs.splitpush >= 4:
                return "스플릿 담당. 사이드 밀다가 텔레포트로 합류."
            if "이니시" in comp_set:
                return "서브 이니시+딜. 탱커 뒤에서 따라 들어가 적 후방을 위협하세요."
            if "한타" in comp_set:
                return "프론트라인. 앞에서 적 스킬 흡수하고 원딜과 너무 떨어지지 마세요."
            if "스커미시" in comp_set:
                return "소규모 교전 주도. 1v1, 2v2에서 이기고 골드 차이를 벌리세요."
            return "서브 탱커/딜러. 상황에 따라 프론트 또는 플랭크로 전환하세요."

        # MAGE
        if "MAGE" in role_tags:
            if "포킹" in comp_set and attrs.poke >= 3:
                return "포킹 담당. 스킬 빗나가면 안 됩니다. 마나 관리 중요."
            if "궁합" in comp_set:
                return "광역 궁극기 담당. 이니시 타이밍에 맞춰 궁을 사용하세요."
            if "한타" in comp_set:
                return "광역 딜러. 안전 거리에서 스킬로 광역 딜링. 포지셔닝 유지."
            if "이니시" in comp_set:
                return "팔로업 딜러. 탱커 이니시 후 광역 스킬로 후속 딜을 넣으세요."
            return "마법 딜러. 스킬 적중률을 높이고 팀파이트에서 광역 딜을 넣으세요."

        # SUPPORT / ENCHANTER
        if "SUPPORT" in role_tags or "ENCHANTER" in role_tags:
            if "프로텍트" in comp_set:
                return "원딜 보호 담당. 보호막/힐/CC로 원딜이 안전하게 딜할 수 있게 하세요."
            if "디스인게이지" in comp_set:
                return "디스인게이지 담당. 적의 돌진을 차단하고 아군을 보호하세요."
            if attrs.peel >= 3:
                return "원딜 보호 담당. 적 다이버/어쌔신 차단이 최우선."
            return "아군 지원 담당. 시야 확보와 CC로 팀을 도우세요."

        return "팀 내 역할을 수행하세요."

    def _build_general_guide(
        self,
        engage: int, peel: int, poke: int, teamfight: int,
        splitpush: int, burst: int, pick: int,
        has_frontline: bool, n: int,
        weaknesses: list[str], strengths: list[str],
    ) -> str:
        """뚜렷한 조합 유형이 없을 때 약점/강점 기반 전체 운영 가이드 생성."""
        lines: list[str] = ["[전체 운영 가이드]"]

        # 이니시 부족 → 정면 한타 피하기
        if engage < 2 * n:
            lines.append("• 이니시 수단이 부족합니다. 정면 5v5를 피하고 소규모 교전이나 오브젝트 주변 소모전을 노리세요.")
            if poke >= 2.5 * n:
                lines.append("  → 포킹 능력이 있으니 오브젝트 앞에서 스킬로 적 체력을 깎은 뒤 진입하세요.")
            if pick >= 2.5 * n:
                lines.append("  → 시야를 장악하고 고립된 적을 캐치하여 숫자 우위를 만드세요.")
            if splitpush >= 2.5 * n:
                lines.append("  → 스플릿으로 적을 분산시킨 후 소규모 교전에서 승리하세요.")
            if burst >= 3 * n:
                lines.append("  → 안개 속 매복으로 핵심 타겟을 순삭한 뒤 오브젝트로 전환하세요.")

        # 필링 부족 → 원딜 보호 어려움
        if peel < 1.5 * n:
            lines.append("• 원딜 보호 수단이 부족합니다. 원딜은 포지셔닝에 각별히 주의하고, 적 어쌔신의 접근을 경계하세요.")

        # 팀파이트 약 → 한타 피하기
        if teamfight < 3 * n and engage >= 2 * n:
            lines.append("• 한타 능력이 약하지만 이니시는 가능합니다. 소수 교전에서 이기고 빠르게 오브젝트를 가져가세요.")

        # 특별한 약점이 없으면 일반 가이드
        if len(lines) == 1:
            lines.append("• 뚜렷한 강점/약점이 없는 균형 조합입니다. 상대 조합의 약점을 파악하고 그에 맞춰 플레이하세요.")
            if has_frontline:
                lines.append("• 프론트라인이 있으니 오브젝트 앞 5v5에서 정면 교전도 가능합니다.")
            lines.append("• 초반 라인전에서 우위를 잡고 오브젝트 주도권을 확보하세요.")

        # 승리 조건 제안
        lines.append("")
        lines.append("[승리 조건]")
        if splitpush >= 3 * n:
            lines.append("• 사이드 압박으로 적을 분산시키고 오브젝트를 확보하세요.")
        elif burst >= 3 * n:
            lines.append("• 핵심 타겟을 빠르게 제거하고 숫자 우위로 오브젝트를 가져가세요.")
        elif teamfight >= 3.5 * n and has_frontline:
            lines.append("• 오브젝트 앞에서 정면 한타를 유도하세요. 프론트라인이 버텨주는 동안 원딜이 딜을 넣습니다.")
        else:
            lines.append("• 소규모 교전에서 이기고 이점을 오브젝트로 전환하세요. 불리한 정면 한타는 피하세요.")

        return "\n".join(lines)

    def _build_champion_roles_guide(
        self,
        assignments: list[Assignment],
        champion_attrs_map: dict[str, ChampionAttributes],
        comp_types: list[str],
    ) -> str:
        """Generate per-champion role descriptions within the team context."""
        if not assignments:
            return ""

        lane_ko_map = {"TOP": "탑", "JG": "정글", "MID": "미드", "ADC": "원딜", "SUP": "서폿"}
        lines: list[str] = ["\n[챔피언별 역할]"]

        for a in assignments:
            attrs = champion_attrs_map.get(a.champion_name)
            lane_ko = lane_ko_map.get(a.lane, a.lane)
            name_ko = attrs.display_name if attrs else a.champion_name
            tips = attrs.play_tips if attrs and attrs.play_tips else ""

            role_desc = self._get_champion_comp_role(a, attrs, comp_types)

            lines.append(f"\u2022 {name_ko} ({lane_ko}): {role_desc}")
            if tips:
                lines.append(f"  팁: {tips}")

        return "\n".join(lines)

    def _detect_comp_types(
        self, champion_attrs_list: list[ChampionAttributes]
    ) -> list[str]:
        """Detect composition archetypes from champion attributes.

        Returns a list of detected comp type names (Korean).
        기준값은 인원수(n) 기반 상대적 판별 (5명 기준 예시):
        1. 이니시: engage >= 3*n (15)
        2. 디스인게이지: peel >= 3*n (15), engage < 2*n (10)
        3. 포킹: poke >= 3*n (15)
        4. 픽: pick >= 3.5*n (17.5)
        5. 스플릿: splitpush >= 3*n (15), 스플릿러 1명+
        6. 한타: teamfight >= 4*n (20), 프론트라인 있음
        7. 프로텍트: peel >= 2.5*n (12.5), 원딜 있음
        8. 다이브: engage >= 2.5*n, burst >= 3*n, peel < 1.5*n
        9. 스커미시: 어쌔신/브루저 3명+ (4명 이상일 때만)
        10. 궁합: engage >= 2.5*n, teamfight >= 3.5*n
        11. 글로벌: 미구현
        12. 폭딜: burst >= 3.5*n, 어쌔신 2명+
        """
        if not champion_attrs_list:
            return []

        engage_total = sum(a.engage for a in champion_attrs_list)
        peel_total = sum(a.peel for a in champion_attrs_list)
        poke_total = sum(a.poke for a in champion_attrs_list)
        pick_total = sum(a.pick for a in champion_attrs_list)
        burst_total = sum(a.burst for a in champion_attrs_list)
        splitpush_total = sum(a.splitpush for a in champion_attrs_list)
        teamfight_total = sum(a.teamfight for a in champion_attrs_list)

        has_frontline = any(
            "TANK" in a.role_tags or "BRUISER" in a.role_tags
            for a in champion_attrs_list
        )
        has_marksman = any(
            "MARKSMAN" in a.role_tags for a in champion_attrs_list
        )
        assassin_count = sum(
            1 for a in champion_attrs_list if "ASSASSIN" in a.role_tags
        )
        skirmish_count = sum(
            1 for a in champion_attrs_list
            if "ASSASSIN" in a.role_tags or "BRUISER" in a.role_tags
        )

        comp_types: list[str] = []

        # 기준값은 5명 평균 합계 대비 유의미하게 높은 값으로 설정
        # engage 평균합=12, peel=8, poke=10, pick=13, burst=15, split=12, teamfight=17
        n = len(champion_attrs_list)

        # 1. 이니시 조합: engage가 평균(2.4*n) 대비 충분히 높음
        if engage_total >= 3 * n:  # 5명: 15
            comp_types.append("이니시")

        # 2. 디스인게이지 조합: peel 높고 engage 낮음
        if peel_total >= 3 * n and engage_total < 2 * n:
            comp_types.append("디스인게이지")

        # 3. 포킹/시즈 조합: poke가 평균(2.0*n) 대비 높음
        if poke_total >= 3 * n:  # 5명: 15
            comp_types.append("포킹")

        # 4. 픽/캐치 조합: pick이 평균(2.5*n) 대비 높음
        if pick_total >= 3.5 * n:  # 5명: 17.5
            comp_types.append("픽")

        # 5. 스플릿 조합: splitpush 높고 스플릿러 1명+
        if splitpush_total >= 3 * n and any(a.splitpush >= 4 for a in champion_attrs_list):
            comp_types.append("스플릿")

        # 6. 프론트투백 한타 조합: teamfight가 평균(3.4*n) 대비 확실히 높음 + 프론트라인
        if teamfight_total >= 4 * n and has_frontline:  # 5명: 20
            comp_types.append("한타")

        # 7. 프로텍트 조합: peel 높고 원딜 있음
        if peel_total >= 2.5 * n and has_marksman:
            comp_types.append("프로텍트")

        # 8. 다이브 조합: engage+burst 높고 peel 낮음
        if engage_total >= 2.5 * n and burst_total >= 3 * n and peel_total < 1.5 * n:
            comp_types.append("다이브")

        # 9. 스커미시/초반 조합: 3+ champions with ASSASSIN or BRUISER
        if skirmish_count >= 3 and n >= 4:
            comp_types.append("스커미시")

        # 10. 궁합(Wombo) 조합: engage + teamfight 둘 다 높음
        if engage_total >= 2.5 * n and teamfight_total >= 3.5 * n:
            comp_types.append("궁합")

        # 11. 글로벌 조합: skipped for now (no GLOBAL tag)

        # 12. 폭딜/어쌔신 조합: burst 높고 어쌔신 2명+
        if burst_total >= 3.5 * n and assassin_count >= 2:
            comp_types.append("폭딜")

        return comp_types

    def _calculate_penalties(
        self,
        champion_attrs_list: list[ChampionAttributes],
        comp_types: list[str] | None = None,
    ) -> dict[str, int]:
        """Calculate penalty deductions.

        Frontline penalty is conditional based on comp type:
        - Apply for: 이니시, 한타, 프로텍트
        - Do NOT apply for: 포킹, 픽, 폭딜, 다이브
        - Other comps: no penalty either way
        """
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

        # No frontline: -25 (conditional based on comp type)
        has_frontline = any(
            "TANK" in a.role_tags or "BRUISER" in a.role_tags
            for a in champion_attrs_list
        )
        if not has_frontline and len(champion_attrs_list) > 0:
            # Detect comp types if not provided
            if comp_types is None:
                comp_types = self._detect_comp_types(champion_attrs_list)

            comp_type_set = set(comp_types)

            # Check if any detected comp type requires frontline
            needs_frontline = bool(comp_type_set & FRONTLINE_REQUIRED_COMP_TYPES)
            # Check if any detected comp type explicitly doesn't need frontline
            no_frontline_ok = bool(comp_type_set & FRONTLINE_NOT_NEEDED_COMP_TYPES)

            # Apply penalty only if comp needs frontline
            # If comp has types that need frontline, apply penalty
            # If comp has types that don't need frontline, skip penalty
            # If comp has no detected types (균형), no penalty
            if needs_frontline and not no_frontline_ok:
                penalties["no_frontline"] = PENALTY_NO_FRONTLINE

        # Low waveclear: -10
        total_waveclear = self._waveclear_score_value(champion_attrs_list)
        if total_waveclear < 10 and len(champion_attrs_list) > 0:
            penalties["low_waveclear"] = PENALTY_LOW_WAVECLEAR

        # 약점 기반 감점 (4명 이상일 때만)
        n = len(champion_attrs_list)
        if n >= 4:
            engage_total = sum(a.engage for a in champion_attrs_list)
            peel_total = sum(a.peel for a in champion_attrs_list)
            teamfight_total = sum(a.teamfight for a in champion_attrs_list)

            if engage_total < 2 * n:
                penalties["low_engage"] = PENALTY_LOW_ENGAGE
            if peel_total < 1.5 * n:
                penalties["low_peel"] = PENALTY_LOW_PEEL
            if teamfight_total < 3 * n:
                penalties["low_teamfight"] = PENALTY_LOW_TEAMFIGHT

        return penalties

    def calculate_score(
        self,
        assignments: list[Assignment],
        champion_attrs_list: list[ChampionAttributes],
        champion_attrs_map: dict[str, ChampionAttributes] | None = None,
    ) -> float:
        """Calculate total composition score (0-100 minus penalties).

        Weights:
        - Personal mastery: 25%
        - Meta tier: 10%
        - AD/AP balance: 15%
        - Frontline: 15%
        - Deal composition: 15%
        - Waveclear: 10%
        - Splitpush: 10%
        """
        personal = self._personal_mastery_score(assignments)

        # 4명 이하: 팀 조합 평가 불가 → 개인 숙련도 위주
        if len(assignments) < 4:
            return personal

        # Build a map from the list if not provided
        if champion_attrs_map is None:
            champion_attrs_map = {a.champion_name: a for a in champion_attrs_list}

        meta = self._meta_tier_score(assignments, champion_attrs_map)
        ad_ap = self._ad_ap_balance_score(champion_attrs_list)
        frontline = self._frontline_score(champion_attrs_list)
        deal = self._deal_composition_score(champion_attrs_list)
        waveclear = self._waveclear_score(champion_attrs_list)
        splitpush = self._splitpush_score(champion_attrs_list)

        base_score = (
            personal * WEIGHT_PERSONAL_MASTERY
            + meta * WEIGHT_META_TIER
            + ad_ap * WEIGHT_AD_AP_BALANCE
            + frontline * WEIGHT_FRONTLINE
            + deal * WEIGHT_DEAL_COMPOSITION
            + waveclear * WEIGHT_WAVECLEAR
            + splitpush * WEIGHT_SPLITPUSH
        )

        # Detect comp types first, then pass to penalty calculation
        comp_types = self._detect_comp_types(champion_attrs_list)
        penalties = self._calculate_penalties(champion_attrs_list, comp_types)
        penalty_total = sum(penalties.values())

        return max(base_score + penalty_total, 0.0)

    def _build_strategy_guide(self, comp_types: list[str]) -> str:
        """Build strategy guide with synergy awareness.

        1. Check if detected comp types match any synergy pair
        2. If yes, use synergy strategy as primary guide
        3. Append individual type strategies as supplementary info
        """
        if not comp_types:
            return ""

        parts: list[str] = []
        used_synergy_types: set[str] = set()

        # Check for synergy pairs
        comp_type_set = set(comp_types)
        for synergy_pair, synergy_strategy in SYNERGY_STRATEGIES.items():
            if synergy_pair.issubset(comp_type_set):
                parts.append(f"[시너지 전략] {synergy_strategy}")
                used_synergy_types.update(synergy_pair)

        # Add individual type strategies
        for ct in comp_types:
            strategy = COMP_STRATEGIES.get(ct)
            if strategy:
                guide = strategy["guide"]
                win_cond = strategy["win_condition"]
                caution = strategy["caution"]
                parts.append(
                    f"[{ct} 조합]\n"
                    f"운영법: {guide}\n"
                    f"승리 조건: {win_cond}\n"
                    f"주의사항: {caution}"
                )

        return "\n\n".join(parts)

    def analyze(
        self,
        assignments: list[Assignment],
        champion_attrs_list: list[ChampionAttributes],
        champion_attrs_map: dict[str, ChampionAttributes] | None = None,
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
        engage_total = sum(a.engage for a in champion_attrs_list)
        peel_total = sum(a.peel for a in champion_attrs_list)
        poke_total = sum(a.poke for a in champion_attrs_list)
        pick_total = sum(a.pick for a in champion_attrs_list)
        burst_total = sum(a.burst for a in champion_attrs_list)

        # Build per-champion stat contributions
        stat_keys = ["teamfight", "engage", "poke", "pick", "burst", "waveclear", "splitpush", "peel"]
        stat_contributions: dict[str, list[dict]] = {}
        for key in stat_keys:
            contribs = []
            for attrs in champion_attrs_list:
                val = getattr(attrs, key, 0)
                if val > 0:
                    contribs.append({"champion": attrs.display_name, "value": val})
            # Sort by value descending
            contribs.sort(key=lambda x: x["value"], reverse=True)
            stat_contributions[key] = contribs

        # Detect comp types
        comp_types = self._detect_comp_types(champion_attrs_list)

        # 2~3명일 때는 페널티 없음, 조합 유형 판별 스킵
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
                strengths=[],
                weaknesses=[],
                penalties={},
                stat_contributions=stat_contributions,
            )

        # Calculate penalties with comp types (conditional frontline penalty)
        penalties = self._calculate_penalties(champion_attrs_list, comp_types)

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
        # 약점 기준: 평균 이하면 약점 (n 기반 상대적 판별)
        n = total
        if engage_total < 2 * n:  # 평균 2.4*n, 이하면 이니시 부족
            weaknesses.append("이니시에이트 부족 — 한타를 걸기 어려움")
        if teamfight_total < 3 * n:  # 평균 3.4*n
            weaknesses.append("팀파이트 능력 부족")
        if poke_total < 1.5 * n:
            weaknesses.append("포킹 능력 부족")
        if peel_total < 1.5 * n:
            weaknesses.append("필링 부족 — 원딜 보호가 어려움")
        if pick_total < 2 * n:
            weaknesses.append("캐치 능력 부족")

        # Build comp type string and strategy guide
        # Build champion attrs map if not provided
        if champion_attrs_map is None:
            champion_attrs_map = {a.champion_name: a for a in champion_attrs_list}

        if comp_types:
            comp_type = " + ".join(t + " 조합" for t in comp_types)
            strategy_guide = self._build_strategy_guide(comp_types)
            # Append champion-specific roles guide
            champion_roles = self._build_champion_roles_guide(
                assignments, champion_attrs_map, comp_types
            )
            if champion_roles:
                strategy_guide = strategy_guide + "\n" + champion_roles if strategy_guide else champion_roles
        else:
            comp_type = "균형 조합"
            # 뚜렷한 조합 유형이 없을 때 약점 기반 운영 가이드 생성
            general_guide = self._build_general_guide(
                engage_total, peel_total, poke_total, teamfight_total,
                splitpush_total, burst_total, pick_total,
                has_frontline, n, weaknesses, strengths
            )
            champion_roles = self._build_champion_roles_guide(
                assignments, champion_attrs_map, comp_types
            )
            strategy_guide = general_guide
            if champion_roles:
                strategy_guide = strategy_guide + "\n" + champion_roles if strategy_guide else champion_roles

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

        Uses the best lane assignment first. Only falls back to lower-ranked
        assignments if the best one produces fewer than top_n compositions.
        This prevents wrong-lane compositions from outscoring correct ones
        due to team comp analysis.
        """
        player_map: dict[str, Player] = {}
        for p in players:
            key = f"{p.game_name}#{p.tag_line}"
            player_map[key] = p

        all_compositions: list[Composition] = []

        for lane_assignment in lane_assignments:
            # 모든 라인 배정을 전수 탐색 — 가장 높은 점수 조합을 찾기 위해
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

                # primary_lanes에 맞는 챔피언만 사용
                # 전체 풀 탐색 — 숙련도 점수가 자연스럽게 우선순위 결정
                if lane_fit:
                    champion_pools.append(lane_fit)
                else:
                    # 이 라인에 맞는 챔피언이 없음 → 이 라인 배정 스킵, 다음 배정 시도
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
                            champion_name_ko=champ_stats.display_name if champ_stats.champion_name_ko else attrs.display_name,
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

                score = self.calculate_score(assignments, attrs_list, champion_attrs_map)

                # Off-lane penalty: 챔피언이 primary_lanes 밖에서 플레이 시 감점
                off_lane_count = self._count_off_lane_champions(
                    assignments, champion_attrs_map
                )
                score += off_lane_count * PENALTY_OFF_LANE_PER_CHAMPION

                # 라인 배정 보너스 제거 — 개인 숙련도(25%)에서 이미 게임수/승률 반영됨
                # 이중 반영하면 게임수 많은 챔피언이 과도하게 유리해짐

                score = max(score, 0.0)

                # Store lightweight tuple — analyze() deferred to top-N only
                all_compositions.append(
                    (round(score, 1), assignments, attrs_list)
                )

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("총 %d개 조합 생성됨", len(all_compositions))

        # Sort by total_score descending
        all_compositions.sort(key=lambda t: t[0], reverse=True)

        # 상위 10개 조합 로깅 (디버그용)
        for i, (sc, assigns, _) in enumerate(all_compositions[:10]):
            champs = ", ".join(f"{a.display_name}({a.lane})" for a in assigns)
            _logger.info("  생성 조합 #%d: 점수=%.1f | %s", i+1, sc, champs)

        # Diversity filter: 각 추천은 이전 추천과 최소 1개 챔피언이 달라야 함
        selected: list[tuple[float, list[Assignment], list[ChampionAttributes]]] = []
        seen_combos: set[frozenset[str]] = set()
        for comp_tuple in all_compositions:
            if len(selected) >= top_n:
                break
            comp_champs = frozenset(a.champion_name for a in comp_tuple[1])
            # 완전 동일 조합만 제거
            if comp_champs in seen_combos:
                continue
            seen_combos.add(comp_champs)
            selected.append(comp_tuple)

        # analyze() 최적화 — 최종 top-N에 대해서만 호출
        result: list[Composition] = []
        for i, (sc, assigns, attrs_lst) in enumerate(selected):
            analysis = self.analyze(assigns, attrs_lst, champion_attrs_map)
            comp = Composition(
                total_score=sc,
                assignments=assigns,
                team_analysis=analysis,
                rank=i + 1,
            )
            result.append(comp)

        return result
