import logging
import time
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 최근 3개월 이내 매치만 조회 (초 단위)
MATCH_MAX_AGE_SECONDS = 90 * 24 * 60 * 60  # 90일

from domain.models.player import Player, LaneStats, ChampionStats

logger = logging.getLogger(__name__)
from domain.models.match import MatchSummary
from domain.models.champion import ChampionAttributes
from domain.services.player_analysis_service import PlayerAnalysisService
from domain.services.lane_optimizer_service import LaneOptimizerService
from domain.services.comp_optimizer_service import CompOptimizerService
from domain.services.champion_data_service import ChampionDataService
from domain.ports.external.riot_api_port import RiotApiPort
from domain.ports.external.ddragon_port import DataDragonPort

router = APIRouter(prefix="/api", tags=["optimize"])

# Services - set during DI assembly
riot_api: RiotApiPort | None = None
ddragon: DataDragonPort | None = None
player_analysis_service: PlayerAnalysisService | None = None
lane_optimizer_service: LaneOptimizerService | None = None
comp_optimizer_service: CompOptimizerService | None = None
champion_data_service: ChampionDataService | None = None


def init_router(
    riot: RiotApiPort,
    dd: DataDragonPort,
    pa: PlayerAnalysisService,
    lo: LaneOptimizerService,
    co: CompOptimizerService,
    cd: ChampionDataService,
) -> None:
    global riot_api, ddragon, player_analysis_service
    global lane_optimizer_service, comp_optimizer_service, champion_data_service
    riot_api = riot
    ddragon = dd
    player_analysis_service = pa
    lane_optimizer_service = lo
    comp_optimizer_service = co
    champion_data_service = cd


# ── Pydantic request/response models ──────────────────────────────────────


class PlayerInput(BaseModel):
    game_name: str
    tag_line: str


class OptimizeRequest(BaseModel):
    api_key: str
    players: list[PlayerInput] = Field(..., min_length=2, max_length=5)
    match_count: int = Field(default=15, ge=5, le=30)


class AnalyzePlayersRequest(BaseModel):
    api_key: str
    players: list[PlayerInput] = Field(..., min_length=2, max_length=5)
    match_count: int = Field(default=15, ge=5, le=30)


class ChampionStatsData(BaseModel):
    champion_id: int
    champion_name: str
    champion_name_ko: str = ""
    games: int = 0
    wins: int = 0
    win_rate: float = 0.0
    kda: float = 0.0
    mastery_points: int = 0


class LaneStatsData(BaseModel):
    games: int = 0
    wins: int = 0
    win_rate: float = 0.0


class PlayerData(BaseModel):
    game_name: str
    tag_line: str
    tier: str = ""
    rank: str = ""
    lp: int = 0
    profile_icon_id: int = 0
    lane_stats: dict[str, LaneStatsData] = Field(default_factory=dict)
    top_champions: list[ChampionStatsData] = Field(default_factory=list)


class OptimizeCompRequest(BaseModel):
    players: list[PlayerData] = Field(..., min_length=2, max_length=5)
    banned_champions: list[str] = Field(default_factory=list)
    enemy_picks: list[str] = Field(default_factory=list)
    locked_picks: dict[str, str] = Field(default_factory=dict)


# ── Helpers ────────────────────────────────────────────────────────────────


def _serialize_player(player: Player) -> dict:
    return {
        "game_name": player.game_name,
        "tag_line": player.tag_line,
        "tier": player.tier,
        "rank": player.rank,
        "lp": player.lp,
        "profile_icon_id": player.profile_icon_id,
        "lane_stats": {
            lane: {
                "games": stats.games,
                "wins": stats.wins,
                "win_rate": round(stats.win_rate, 3),
            }
            for lane, stats in player.lane_stats.items()
        },
        "top_champions": [
            {
                "champion_id": c.champion_id,
                "champion_name": c.champion_name,
                "champion_name_ko": c.champion_name_ko,
                "games": c.games,
                "wins": c.wins,
                "win_rate": round(c.win_rate, 3),
                "kda": c.kda,
                "mastery_points": c.mastery_points,
            }
            for c in player.top_champions
        ],
    }


def _serialize_recommendations(compositions: list) -> list[dict]:
    """Serialize Composition objects into the API response format."""
    recommendations = []
    for comp in compositions:
        recommendations.append(
            {
                "rank": comp.rank,
                "total_score": comp.total_score,
                "assignments": [
                    {
                        "player": f"{a.player_game_name}#{a.player_tag_line}",
                        "lane": a.lane,
                        "champion": a.champion_name,
                        "champion_name_ko": a.champion_name_ko,
                        "champion_id": a.champion_id,
                        "personal_win_rate": round(a.personal_win_rate, 3),
                        "personal_kda": a.personal_kda,
                    }
                    for a in comp.assignments
                ],
                "team_analysis": {
                    "ad_ratio": comp.team_analysis.ad_ratio,
                    "ap_ratio": comp.team_analysis.ap_ratio,
                    "has_frontline": comp.team_analysis.has_frontline,
                    "waveclear_score": comp.team_analysis.waveclear_score,
                    "splitpush_score": comp.team_analysis.splitpush_score,
                    "teamfight_score": comp.team_analysis.teamfight_score,
                    "engage_score": comp.team_analysis.engage_score,
                    "peel_score": comp.team_analysis.peel_score,
                    "poke_score": comp.team_analysis.poke_score,
                    "pick_score": comp.team_analysis.pick_score,
                    "burst_score": comp.team_analysis.burst_score,
                    "comp_type": comp.team_analysis.comp_type,
                    "strategy_guide": comp.team_analysis.strategy_guide,
                    "strengths": comp.team_analysis.strengths,
                    "weaknesses": comp.team_analysis.weaknesses,
                    "stat_contributions": comp.team_analysis.stat_contributions,
                },
            }
        )
    return recommendations


async def _fetch_players_from_riot(
    player_inputs: list[PlayerInput],
    api_key: str,
    match_count: int,
) -> list[Player]:
    """Fetch player data from Riot API. Shared by /analyze-players and /optimize."""
    if riot_api is None or ddragon is None:
        raise HTTPException(status_code=500, detail="Services not initialized")

    players: list[Player] = []

    # Get Data Dragon champion data for ID -> name mapping
    dd_champions = await ddragon.get_all_champions()
    champion_id_to_name: dict[int, str] = {}
    champion_id_to_name_ko: dict[int, str] = {}
    for key_str, info in dd_champions.items():
        cid = int(key_str)
        champion_id_to_name[cid] = info["id"]
        champion_id_to_name_ko[cid] = info.get("name", "")

    # Also build lookup from champion_attributes.json (DB) for Korean names
    all_attrs = await champion_data_service.get_all() if champion_data_service else []
    champion_name_to_ko: dict[str, str] = {
        a.champion_name: a.champion_name_ko for a in all_attrs if a.champion_name_ko
    }

    total_players = len(player_inputs)

    for idx, player_input in enumerate(player_inputs, start=1):
        player_label = f"{player_input.game_name}#{player_input.tag_line}"
        logger.info("[%d/%d] 플레이어 분석 시작: %s", idx, total_players, player_label)

        try:
            # Get account (puuid)
            account = await riot_api.get_account_by_riot_id(
                player_input.game_name, player_input.tag_line, api_key
            )
            if account is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"소환사를 찾을 수 없습니다: {player_label}",
                )

            puuid = account["puuid"]
            logger.info("  → 계정 정보 조회 완료 (puuid: %s...)", puuid[:8])

            # Get summoner
            summoner = await riot_api.get_summoner_by_puuid(puuid, api_key)
            summoner_id = ""
            profile_icon_id = 0
            if summoner:
                summoner_id = summoner.get("id", summoner.get("encryptedSummonerId", ""))
                profile_icon_id = summoner.get("profileIconId", 0)

            # Get league entries (rank info)
            tier = ""
            rank = ""
            lp = 0
            league_entries = await riot_api.get_league_entries(summoner_id, api_key) if summoner_id else []
            for entry in league_entries:
                if entry.get("queueType") == "RANKED_SOLO_5x5":
                    tier = entry.get("tier", "")
                    rank = entry.get("rank", "")
                    lp = entry.get("leaguePoints", 0)
                    break

            logger.info("  → 소환사 정보 조회 완료 (tier: %s %s)", tier, rank)

            # Get champion masteries
            masteries = await riot_api.get_champion_masteries(puuid, 30, api_key)
            mastery_map: dict[int, int] = {}
            for m in masteries:
                mastery_map[m["championId"]] = m.get("championPoints", 0)

            # Get match IDs from each SR queue (최근 3개월 이내만)
            start_time = int(time.time()) - MATCH_MAX_AGE_SECONDS
            all_match_ids: list[str] = []
            seen: set[str] = set()
            for q in (420, 440, 400, 430):
                ids = await riot_api.get_match_ids(
                    puuid, match_count, q, api_key, start_time=start_time
                )
                for mid in ids:
                    if mid not in seen:
                        seen.add(mid)
                        all_match_ids.append(mid)
            # 최신순 정렬 (매치 ID에 타임스탬프 포함) 후 N개만
            all_match_ids.sort(reverse=True)
            match_ids = all_match_ids[:match_count]
            logger.info("  → 매치 ID %d개 조회 완료 (소환사 협곡만)", len(match_ids))

            # Get match details and build MatchSummary list
            match_summaries: list[MatchSummary] = []
            total_matches = len(match_ids)
            for match_idx, match_id in enumerate(match_ids, start=1):
                logger.info("  → 매치 상세 조회 중... (%d/%d)", match_idx, total_matches)
                detail = await riot_api.get_match_detail(match_id, api_key)
                if detail is None:
                    continue

                info = detail.get("info", {})
                participants = info.get("participants", [])

                player_data = None
                for p in participants:
                    if p.get("puuid") == puuid:
                        player_data = p
                        break

                if player_data is None:
                    continue

                # Detect if player was jungling by checking for Smite (summoner spell ID 11)
                summoner_spell1 = player_data.get("summoner1Id", 0)
                summoner_spell2 = player_data.get("summoner2Id", 0)
                has_smite = summoner_spell1 == 11 or summoner_spell2 == 11

                if has_smite:
                    lane = "JG"
                else:
                    # Use teamPosition as a reference
                    position = player_data.get("teamPosition", "") or player_data.get(
                        "individualPosition", ""
                    )
                    lane = player_analysis_service.normalize_lane(position) if player_analysis_service else position

                champion_id = player_data.get("championId", 0)
                champion_name = champion_id_to_name.get(
                    champion_id, player_data.get("championName", "Unknown")
                )

                logger.info(
                    "    매치 %s: %s (%s) %s",
                    match_id[-8:], champion_name, lane, "승" if player_data.get("win") else "패"
                )

                match_summaries.append(
                    MatchSummary(
                        match_id=match_id,
                        champion_name=champion_name,
                        champion_id=champion_id,
                        lane=lane,
                        win=player_data.get("win", False),
                        kills=player_data.get("kills", 0),
                        deaths=player_data.get("deaths", 0),
                        assists=player_data.get("assists", 0),
                        cs=player_data.get("totalMinionsKilled", 0)
                        + player_data.get("neutralMinionsKilled", 0),
                        game_duration=info.get("gameDuration", 0),
                    )
                )

            # Calculate stats
            lane_stats = (
                player_analysis_service.calculate_lane_stats(match_summaries)
                if player_analysis_service
                else {}
            )
            champion_stats = (
                player_analysis_service.calculate_champion_stats(match_summaries)
                if player_analysis_service
                else []
            )

            logger.info(
                "  → 챔피언 통계 계산 완료 (챔피언 %d개, 라인 %d개)",
                len(champion_stats),
                len(lane_stats),
            )

            # Add mastery points and Korean names to champion stats
            for cs in champion_stats:
                cs.mastery_points = mastery_map.get(cs.champion_id, 0)
                cs.champion_name_ko = (
                    champion_name_to_ko.get(cs.champion_name, "")
                    or champion_id_to_name_ko.get(cs.champion_id, "")
                )

            # 매치 기반 챔피언이 부족하면 숙련도(모스트) 데이터로 보충
            MIN_CHAMPION_POOL = 5
            if len(champion_stats) < MIN_CHAMPION_POOL:
                existing_champ_ids = {cs.champion_id for cs in champion_stats}
                # mastery_map is already sorted by points (API returns top 30 by mastery)
                for m in masteries:
                    if len(champion_stats) >= MIN_CHAMPION_POOL:
                        break
                    champ_id = m["championId"]
                    if champ_id in existing_champ_ids:
                        continue
                    champ_name = champion_id_to_name.get(champ_id, f"Champion_{champ_id}")
                    mastery_pts = m.get("championPoints", 0)
                    champ_name_ko = (
                        champion_name_to_ko.get(champ_name, "")
                        or champion_id_to_name_ko.get(champ_id, "")
                    )
                    champion_stats.append(
                        ChampionStats(
                            champion_id=champ_id,
                            champion_name=champ_name,
                            champion_name_ko=champ_name_ko,
                            games=0,
                            wins=0,
                            win_rate=0.5,  # 매치 데이터 없으므로 중립 승률
                            kda=0.0,
                            mastery_points=mastery_pts,
                        )
                    )
                    existing_champ_ids.add(champ_id)
                logger.info(
                    "  → 숙련도 데이터로 챔피언 풀 보충 (최종 %d개)",
                    len(champion_stats),
                )

            player = Player(
                game_name=player_input.game_name,
                tag_line=player_input.tag_line,
                puuid=puuid,
                summoner_id=summoner_id,
                tier=tier,
                rank=rank,
                lp=lp,
                profile_icon_id=profile_icon_id,
                lane_stats=lane_stats,
                top_champions=champion_stats,
            )
            players.append(player)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "플레이어 %s 분석 중 오류 발생: %s\n%s",
                player_label,
                str(e),
                traceback.format_exc(),
            )
            raise HTTPException(
                status_code=500,
                detail=f"플레이어 분석 중 오류: {player_label}",
            )

    return players


async def _run_optimization(players: list[Player]) -> list:
    """Run lane + comp optimization on Player objects. Returns Composition list."""
    if riot_api is None or ddragon is None:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # Get Data Dragon tags for fallback attribute generation
    dd_champions = await ddragon.get_all_champions()
    champion_id_to_tags: dict[int, list[str]] = {}
    for key_str, info in dd_champions.items():
        cid = int(key_str)
        champion_id_to_tags[cid] = info.get("tags", [])

    # Build champion attributes map (needed for lane inference)
    all_attrs = await champion_data_service.get_all()
    champion_attrs_map: dict[str, ChampionAttributes] = {
        a.champion_name: a for a in all_attrs
    }

    # For any champion in player pools not in the map, add auto-generated attrs
    for player in players:
        logger.info(
            "  플레이어 %s#%s 챔피언풀: %d개 [%s]",
            player.game_name, player.tag_line,
            len(player.top_champions),
            ", ".join(c.champion_name for c in player.top_champions[:10]),
        )
        for cs in player.top_champions:
            if cs.champion_name not in champion_attrs_map:
                tags = champion_id_to_tags.get(cs.champion_id, ["Fighter"])
                auto_attrs = champion_data_service.get_attributes_with_fallback(
                    champion_name=cs.champion_name,
                    ddragon_tags=tags,
                    champion_id=cs.champion_id,
                )
                champion_attrs_map[cs.champion_name] = auto_attrs

    # Run lane optimizer (with champion pool inference for sparse lane_stats)
    lane_assignments = lane_optimizer_service.optimize(
        players, top_n=3, champion_attrs_map=champion_attrs_map,
    )

    # Run comp optimizer
    compositions = comp_optimizer_service.optimize(
        players=players,
        lane_assignments=lane_assignments,
        champion_attrs_map=champion_attrs_map,
        top_n=5,
    )

    return compositions


def _player_data_to_domain(player_data: PlayerData) -> Player:
    """Convert Pydantic PlayerData to domain Player object."""
    lane_stats: dict[str, LaneStats] = {}
    for lane, stats in player_data.lane_stats.items():
        lane_stats[lane] = LaneStats(
            games=stats.games,
            wins=stats.wins,
            win_rate=stats.win_rate,
        )

    top_champions: list[ChampionStats] = []
    for c in player_data.top_champions:
        top_champions.append(
            ChampionStats(
                champion_id=c.champion_id,
                champion_name=c.champion_name,
                champion_name_ko=c.champion_name_ko,
                games=c.games,
                wins=c.wins,
                win_rate=c.win_rate,
                kda=c.kda,
                mastery_points=c.mastery_points,
            )
        )

    return Player(
        game_name=player_data.game_name,
        tag_line=player_data.tag_line,
        tier=player_data.tier,
        rank=player_data.rank,
        lp=player_data.lp,
        profile_icon_id=player_data.profile_icon_id,
        lane_stats=lane_stats,
        top_champions=top_champions,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/analyze-players")
async def analyze_players(request: AnalyzePlayersRequest) -> dict:
    """Step 1: Fetch and analyze player data from Riot API (slow).

    Returns player objects with lane_stats and top_champions.
    """
    players = await _fetch_players_from_riot(
        request.players, request.api_key, request.match_count
    )
    return {"players": [_serialize_player(p) for p in players]}


@router.post("/optimize-comp")
async def optimize_comp(request: OptimizeCompRequest) -> dict:
    """Step 2: Run pure optimization on pre-analyzed player data (fast, repeatable).

    Accepts player data directly (no Riot API calls).
    Supports banned_champions, enemy_picks, and locked_picks.
    """
    if champion_data_service is None or lane_optimizer_service is None or comp_optimizer_service is None:
        raise HTTPException(status_code=500, detail="Services not initialized")

    logger.info(
        "조합 최적화 시작 (밴: %d개, 적픽: %d개, 고정픽: %d개)",
        len(request.banned_champions),
        len(request.enemy_picks),
        len(request.locked_picks),
    )

    # Convert PlayerData to domain Player objects
    players = [_player_data_to_domain(pd) for pd in request.players]

    # Collect all champion names to exclude (bans + enemy picks)
    excluded_champions: set[str] = set(request.banned_champions) | set(request.enemy_picks)

    # Filter excluded champions from each player's pool
    for player in players:
        player.top_champions = [
            c for c in player.top_champions
            if c.champion_name not in excluded_champions
        ]

    # Handle locked picks: force the locked champion for that player
    locked_player_keys: set[str] = set()
    for player_key, champion_name in request.locked_picks.items():
        locked_player_keys.add(player_key)
        # Find the player
        for player in players:
            key = f"{player.game_name}#{player.tag_line}"
            if key == player_key:
                # Find the champion in their pool
                locked_champ = None
                for c in player.top_champions:
                    if c.champion_name == champion_name:
                        locked_champ = c
                        break
                # If champion not in pool, create a placeholder entry
                if locked_champ is None:
                    locked_champ = ChampionStats(
                        champion_name=champion_name,
                        games=0,
                        wins=0,
                        win_rate=0.0,
                        kda=0.0,
                    )
                # Set the player's pool to only the locked champion
                player.top_champions = [locked_champ]
                break

    # Build champion attributes map from DB
    all_attrs = await champion_data_service.get_all()
    champion_attrs_map: dict[str, ChampionAttributes] = {
        a.champion_name: a for a in all_attrs
    }

    # Get Data Dragon tags for fallback attribute generation
    dd_champions = await ddragon.get_all_champions()
    champion_id_to_tags: dict[int, list[str]] = {}
    for key_str, info in dd_champions.items():
        cid = int(key_str)
        champion_id_to_tags[cid] = info.get("tags", [])

    # For any champion in player pools not in the map, add auto-generated attrs
    for player in players:
        for cs in player.top_champions:
            if cs.champion_name not in champion_attrs_map:
                tags = champion_id_to_tags.get(cs.champion_id, ["Fighter"])
                auto_attrs = champion_data_service.get_attributes_with_fallback(
                    champion_name=cs.champion_name,
                    ddragon_tags=tags,
                    champion_id=cs.champion_id,
                )
                champion_attrs_map[cs.champion_name] = auto_attrs

    # Build lane constraints from locked picks
    # 허용 라인 = 챔피언의 primary_lanes + 플레이어가 실제 플레이한 라인
    lane_constraints: dict[str, list[str]] = {}
    for player_key, champion_name in request.locked_picks.items():
        attrs = champion_attrs_map.get(champion_name)
        allowed = set(attrs.primary_lanes) if attrs and attrs.primary_lanes else set(LANES)
        # 플레이어가 실제 플레이한 라인도 추가 (판테온 정글 등)
        for player in players:
            key = f"{player.game_name}#{player.tag_line}"
            if key == player_key:
                for lane in player.lane_stats:
                    if player.lane_stats[lane].games >= 1:
                        allowed.add(lane)
                break
        lane_constraints[player_key] = list(allowed)
        logger.info(
            "  라인 제약: %s → %s (허용: %s)",
            player_key, champion_name, lane_constraints[player_key]
        )

    # Log player lane stats for debugging
    for player in players:
        key = f"{player.game_name}#{player.tag_line}"
        stats_str = ", ".join(
            f"{lane}: {s.games}판 {s.win_rate:.0%}"
            for lane, s in sorted(player.lane_stats.items(), key=lambda x: x[1].games, reverse=True)
        )
        logger.info("  플레이어 라인 통계: %s → %s", key, stats_str or "(없음)")

    # Run lane optimizer (with lane constraints for locked picks)
    lane_assignments = lane_optimizer_service.optimize(
        players, top_n=3, lane_constraints=lane_constraints,
        champion_attrs_map=champion_attrs_map,
    )

    # Log lane assignment results
    for i, la in enumerate(lane_assignments[:3]):
        assign_str = ", ".join(f"{a.player_game_name}→{a.lane}" for a in la.assignments)
        logger.info("  라인배정 #%d (점수 %.3f): %s", i + 1, la.score, assign_str)

    # Run comp optimizer
    compositions = comp_optimizer_service.optimize(
        players=players,
        lane_assignments=lane_assignments,
        champion_attrs_map=champion_attrs_map,
        top_n=5,
    )

    return {"recommendations": _serialize_recommendations(compositions)}


@router.post("/optimize")
async def optimize(request: OptimizeRequest) -> dict:
    """Full optimization flow (backward compatible):
    1. Fetch player data from Riot API
    2. Run lane + comp optimization
    3. Return players + recommendations
    """
    players = await _fetch_players_from_riot(
        request.players, request.api_key, request.match_count
    )
    compositions = await _run_optimization(players)

    return {
        "players": [_serialize_player(p) for p in players],
        "recommendations": _serialize_recommendations(compositions),
    }
