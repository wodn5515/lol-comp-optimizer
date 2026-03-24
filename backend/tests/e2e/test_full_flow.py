"""E2E tests for the full LoL Comp Optimizer flow.

Covers the 2-step architecture (analyze-players -> optimize-comp),
legacy single-shot API, ban/pick constraints, and error cases.
"""

import pytest
from httpx import AsyncClient

from tests.integration.conftest import MockRiotApi


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_player_data(
    game_name: str,
    tag_line: str,
    champions: list[dict],
    lane_stats: dict | None = None,
) -> dict:
    if lane_stats is None:
        lane_stats = {
            "TOP": {"games": 5, "wins": 3, "win_rate": 0.6},
            "MID": {"games": 3, "wins": 2, "win_rate": 0.667},
        }
    return {
        "game_name": game_name,
        "tag_line": tag_line,
        "tier": "GOLD",
        "rank": "II",
        "lp": 50,
        "profile_icon_id": 1234,
        "lane_stats": lane_stats,
        "top_champions": champions,
    }


# ── Scenario 1: Analyze -> BanPick -> Result ────────────────────────────────


@pytest.mark.asyncio
async def test_scenario1_analyze_then_optimize(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Full 2-step flow: analyze-players (2 players) then optimize-comp."""

    # Step 1: POST /api/analyze-players with 2 players
    analyze_resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "PlayerB", "tag_line": "KR2"},
            ],
            "match_count": 5,
        },
    )
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.json()

    # Verify 2 players returned
    assert len(analyze_data["players"]) == 2

    # Each player must have lane_stats and top_champions
    for player in analyze_data["players"]:
        assert "lane_stats" in player
        assert "top_champions" in player
        assert isinstance(player["lane_stats"], dict)
        assert isinstance(player["top_champions"], list)
        assert len(player["top_champions"]) > 0

    # Step 2: POST /api/optimize-comp (no bans)
    opt_resp = await client.post(
        "/api/optimize-comp",
        json={"players": analyze_data["players"]},
    )
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()

    # At least 1 recommendation with total_score > 0
    assert len(opt_data["recommendations"]) >= 1
    rec = opt_data["recommendations"][0]
    assert rec["total_score"] > 0

    # comp_type and strategy_guide must be present
    ta = rec["team_analysis"]
    assert "comp_type" in ta
    assert isinstance(ta["comp_type"], str)
    # 2명일 때 comp_type은 빈 문자열 (팀 조합 판별 불가)
    assert "strategy_guide" in ta
    assert isinstance(ta["strategy_guide"], str)
    # Note: strategy_guide may be empty for small teams (2 players)
    # since archetype thresholds are calibrated for 5-player compositions

    # ad_ratio + ap_ratio should sum to ~1.0
    assert ta["ad_ratio"] + ta["ap_ratio"] == pytest.approx(1.0, abs=0.01)


# ── Scenario 2: Bans / Enemy Picks / Locked Picks ───────────────────────────


@pytest.mark.asyncio
async def test_scenario2_ban_pick_constraints(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Bans, enemy picks, and locked picks are all respected."""

    # Step 1: Analyze 3 players
    analyze_resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "PlayerB", "tag_line": "KR2"},
                {"game_name": "PlayerC", "tag_line": "KR3"},
            ],
            "match_count": 5,
        },
    )
    assert analyze_resp.status_code == 200
    players = analyze_resp.json()["players"]
    assert len(players) == 3

    # --- 2a: Ban Aatrox → Aatrox must not appear in any recommendation ---
    resp_ban = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "banned_champions": ["Aatrox"],
        },
    )
    assert resp_ban.status_code == 200
    for rec in resp_ban.json()["recommendations"]:
        for a in rec["assignments"]:
            assert a["champion"] != "Aatrox", "Banned champion Aatrox should not appear"

    # --- 2b: Enemy picked Viktor → Viktor must not appear ---
    resp_enemy = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "enemy_picks": ["Viktor"],
        },
    )
    assert resp_enemy.status_code == 200
    for rec in resp_enemy.json()["recommendations"]:
        for a in rec["assignments"]:
            assert a["champion"] != "Viktor", "Enemy-picked Viktor should not appear"

    # --- 2c: Lock PlayerA#KR1 to Jinx → PlayerA always plays Jinx ---
    resp_lock = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "locked_picks": {"PlayerA#KR1": "Jinx"},
        },
    )
    assert resp_lock.status_code == 200
    for rec in resp_lock.json()["recommendations"]:
        for a in rec["assignments"]:
            if a["player"] == "PlayerA#KR1":
                assert a["champion"] == "Jinx", (
                    f"PlayerA should be locked to Jinx, got {a['champion']}"
                )


# ── Scenario 3: Legacy /api/optimize compatibility ──────────────────────────


@pytest.mark.asyncio
async def test_scenario3_legacy_optimize(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Legacy single-shot POST /api/optimize still works end-to-end."""
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "PlayerB", "tag_line": "KR2"},
            ],
            "match_count": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Must have both players and recommendations
    assert "players" in data
    assert "recommendations" in data
    assert len(data["players"]) == 2
    assert len(data["recommendations"]) >= 1

    rec = data["recommendations"][0]
    assert rec["total_score"] > 0
    assert len(rec["assignments"]) == 2
    assert "team_analysis" in rec

    ta = rec["team_analysis"]
    assert ta["ad_ratio"] + ta["ap_ratio"] == pytest.approx(1.0, abs=0.01)
    assert "comp_type" in ta
    assert "strategy_guide" in ta


# ── Scenario 4: Error cases ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scenario4_not_found_summoner(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Nonexistent summoner returns 404."""
    mock_riot_api.set_not_found("GhostPlayer", "9999")
    resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "GhostPlayer", "tag_line": "9999"},
            ],
            "match_count": 5,
        },
    )
    assert resp.status_code == 404
    assert "소환사를 찾을 수 없습니다" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_scenario4_too_few_players_analyze(client: AsyncClient) -> None:
    """Only 1 player in analyze-players returns 422 (min 2 required)."""
    resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [{"game_name": "Solo", "tag_line": "KR1"}],
            "match_count": 5,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_scenario4_empty_players_optimize_comp(client: AsyncClient) -> None:
    """Empty players list in optimize-comp returns 422."""
    resp = await client.post(
        "/api/optimize-comp",
        json={"players": []},
    )
    assert resp.status_code == 422


# ── Additional E2E assertions ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_flow_team_analysis_fields(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Verify all team_analysis fields are present and correctly typed."""
    analyze_resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "PlayerB", "tag_line": "KR2"},
            ],
            "match_count": 5,
        },
    )
    assert analyze_resp.status_code == 200

    opt_resp = await client.post(
        "/api/optimize-comp",
        json={"players": analyze_resp.json()["players"]},
    )
    assert opt_resp.status_code == 200

    rec = opt_resp.json()["recommendations"][0]
    ta = rec["team_analysis"]

    # All expected fields
    expected_fields = [
        "ad_ratio", "ap_ratio", "has_frontline", "waveclear_score",
        "splitpush_score", "teamfight_score", "engage_score", "peel_score",
        "poke_score", "pick_score", "burst_score", "comp_type",
        "strategy_guide", "strengths", "weaknesses",
    ]
    for field in expected_fields:
        assert field in ta, f"Missing team_analysis field: {field}"

    # Type checks
    assert isinstance(ta["ad_ratio"], (int, float))
    assert isinstance(ta["ap_ratio"], (int, float))
    assert isinstance(ta["has_frontline"], bool)
    assert isinstance(ta["strengths"], list)
    assert isinstance(ta["weaknesses"], list)
    assert isinstance(ta["comp_type"], str)
    assert isinstance(ta["strategy_guide"], str)


@pytest.mark.asyncio
async def test_full_flow_assignment_structure(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Verify assignment fields in the recommendation."""
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "PlayerB", "tag_line": "KR2"},
            ],
            "match_count": 5,
        },
    )
    assert resp.status_code == 200
    rec = resp.json()["recommendations"][0]

    for a in rec["assignments"]:
        assert "player" in a
        assert "lane" in a
        assert "champion" in a
        assert "champion_id" in a
        assert "personal_win_rate" in a
        assert "personal_kda" in a
        assert a["lane"] in {"TOP", "JG", "MID", "ADC", "SUP"}
        assert isinstance(a["personal_win_rate"], (int, float))
        assert 0.0 <= a["personal_win_rate"] <= 1.0
