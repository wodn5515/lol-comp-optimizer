import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.integration.conftest import MockRiotApi


@pytest.mark.asyncio
async def test_optimize_full_flow(client: AsyncClient, mock_riot_api: MockRiotApi) -> None:
    """Full optimization flow: input -> Riot API query -> analysis -> recommendation."""
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

    # Player info returned
    assert len(data["players"]) == 2
    assert data["players"][0]["tier"] == "GOLD"
    assert data["players"][0]["rank"] == "II"
    assert data["players"][0]["lp"] == 50

    # Recommendations returned
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["total_score"] > 0
    assert len(rec["assignments"]) == 2

    # Team analysis has valid AD/AP ratio
    ta = rec["team_analysis"]
    assert ta["ad_ratio"] + ta["ap_ratio"] == pytest.approx(1.0, abs=0.01)
    assert isinstance(ta["has_frontline"], bool)
    assert isinstance(ta["waveclear_score"], int)
    assert isinstance(ta["strengths"], list)
    assert isinstance(ta["weaknesses"], list)

    # New archetype fields present
    assert "engage_score" in ta
    assert "peel_score" in ta
    assert "poke_score" in ta
    assert "pick_score" in ta
    assert "burst_score" in ta
    assert "comp_type" in ta
    assert isinstance(ta["comp_type"], str)
    assert ta["comp_type"] != ""
    assert "strategy_guide" in ta
    assert isinstance(ta["strategy_guide"], str)


@pytest.mark.asyncio
async def test_optimize_invalid_summoner(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Nonexistent summoner should return 404."""
    mock_riot_api.set_not_found("Unknown", "0000")
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": [{"game_name": "Unknown", "tag_line": "0000"}],
            "match_count": 5,
        },
    )
    # Note: min_length=2 on players means this gets a 422 first.
    # Let's test with 2 players where one is not found.


@pytest.mark.asyncio
async def test_optimize_one_invalid_summoner(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """One invalid summoner in a group should return 404."""
    mock_riot_api.set_not_found("Unknown", "0000")
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "Unknown", "tag_line": "0000"},
            ],
            "match_count": 5,
        },
    )
    assert resp.status_code == 404
    assert "소환사를 찾을 수 없습니다" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_optimize_too_few_players(client: AsyncClient) -> None:
    """Less than 2 players should return 422."""
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": [{"game_name": "Solo", "tag_line": "KR1"}],
            "match_count": 5,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_optimize_too_many_players(client: AsyncClient) -> None:
    """More than 5 players should return 422."""
    players = [
        {"game_name": f"Player{i}", "tag_line": "KR1"} for i in range(6)
    ]
    resp = await client.post(
        "/api/optimize",
        json={
            "api_key": "test-key",
            "players": players,
            "match_count": 5,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_optimize_response_structure(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Verify response matches the spec format."""
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

    # Check player structure
    player = data["players"][0]
    assert "game_name" in player
    assert "tag_line" in player
    assert "tier" in player
    assert "rank" in player
    assert "lp" in player
    assert "profile_icon_id" in player
    assert "lane_stats" in player
    assert "top_champions" in player

    # Check recommendation structure
    rec = data["recommendations"][0]
    assert "rank" in rec
    assert "total_score" in rec
    assert "assignments" in rec
    assert "team_analysis" in rec

    # Check assignment structure
    assignment = rec["assignments"][0]
    assert "player" in assignment
    assert "lane" in assignment
    assert "champion" in assignment
    assert "champion_id" in assignment
    assert "personal_win_rate" in assignment
    assert "personal_kda" in assignment


# ── POST /api/analyze-players tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_players(client: AsyncClient, mock_riot_api: MockRiotApi) -> None:
    """Analyze players returns player data with lane_stats and top_champions."""
    resp = await client.post(
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
    assert resp.status_code == 200
    data = resp.json()

    # Should return players array only (no recommendations)
    assert "players" in data
    assert "recommendations" not in data
    assert len(data["players"]) == 2

    player = data["players"][0]
    assert player["game_name"] == "PlayerA"
    assert player["tag_line"] == "KR1"
    assert player["tier"] == "GOLD"
    assert player["rank"] == "II"
    assert player["lp"] == 50
    assert "lane_stats" in player
    assert "top_champions" in player
    assert len(player["top_champions"]) > 0


@pytest.mark.asyncio
async def test_analyze_players_invalid_summoner(
    client: AsyncClient, mock_riot_api: MockRiotApi
) -> None:
    """Analyze with invalid summoner returns 404."""
    mock_riot_api.set_not_found("Unknown", "0000")
    resp = await client.post(
        "/api/analyze-players",
        json={
            "api_key": "test-key",
            "players": [
                {"game_name": "PlayerA", "tag_line": "KR1"},
                {"game_name": "Unknown", "tag_line": "0000"},
            ],
            "match_count": 5,
        },
    )
    assert resp.status_code == 404
    assert "소환사를 찾을 수 없습니다" in resp.json()["detail"]


# ── POST /api/optimize-comp tests ──────────────────────────────────────────


def _make_player_data(
    game_name: str,
    tag_line: str,
    champions: list[dict],
    lane_stats: dict | None = None,
) -> dict:
    """Helper to build player data dict for optimize-comp requests."""
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


@pytest.mark.asyncio
async def test_optimize_comp_basic(client: AsyncClient) -> None:
    """Basic optimize-comp returns recommendations without Riot API calls."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
            {"champion_id": 112, "champion_name": "Viktor", "games": 5, "wins": 3, "win_rate": 0.6, "kda": 2.5, "mastery_points": 50000},
        ], lane_stats={
            "TOP": {"games": 10, "wins": 7, "win_rate": 0.7},
            "MID": {"games": 5, "wins": 3, "win_rate": 0.6},
        }),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
            {"champion_id": 412, "champion_name": "Thresh", "games": 6, "wins": 4, "win_rate": 0.667, "kda": 3.5, "mastery_points": 60000},
        ], lane_stats={
            "ADC": {"games": 8, "wins": 5, "win_rate": 0.625},
            "SUP": {"games": 6, "wins": 4, "win_rate": 0.667},
        }),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={"players": players},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["total_score"] > 0
    assert len(rec["assignments"]) == 2
    assert "team_analysis" in rec


@pytest.mark.asyncio
async def test_optimize_comp_with_bans(client: AsyncClient) -> None:
    """Banned champions should be excluded from all player pools."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
            {"champion_id": 112, "champion_name": "Viktor", "games": 5, "wins": 3, "win_rate": 0.6, "kda": 2.5, "mastery_points": 50000},
        ]),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
            {"champion_id": 412, "champion_name": "Thresh", "games": 6, "wins": 4, "win_rate": 0.667, "kda": 3.5, "mastery_points": 60000},
        ]),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "banned_champions": ["Aatrox"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Aatrox should not appear in any assignment
    for rec in data["recommendations"]:
        for assignment in rec["assignments"]:
            assert assignment["champion"] != "Aatrox", "Banned champion Aatrox should not be picked"


@pytest.mark.asyncio
async def test_optimize_comp_with_enemy_picks(client: AsyncClient) -> None:
    """Enemy-picked champions should be excluded from our pools."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
            {"champion_id": 112, "champion_name": "Viktor", "games": 5, "wins": 3, "win_rate": 0.6, "kda": 2.5, "mastery_points": 50000},
        ]),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
            {"champion_id": 412, "champion_name": "Thresh", "games": 6, "wins": 4, "win_rate": 0.667, "kda": 3.5, "mastery_points": 60000},
        ]),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "enemy_picks": ["Jinx", "Viktor"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Jinx and Viktor should not appear in any assignment
    for rec in data["recommendations"]:
        for assignment in rec["assignments"]:
            assert assignment["champion"] not in ("Jinx", "Viktor"), \
                f"Enemy-picked champion {assignment['champion']} should not be in our comp"


@pytest.mark.asyncio
async def test_optimize_comp_with_locked_picks(client: AsyncClient) -> None:
    """Locked picks should force that champion for the specified player."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
            {"champion_id": 112, "champion_name": "Viktor", "games": 5, "wins": 3, "win_rate": 0.6, "kda": 2.5, "mastery_points": 50000},
        ]),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
            {"champion_id": 412, "champion_name": "Thresh", "games": 6, "wins": 4, "win_rate": 0.667, "kda": 3.5, "mastery_points": 60000},
        ]),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "locked_picks": {"PlayerA#KR1": "Viktor"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # In every recommendation, PlayerA should be assigned Viktor
    for rec in data["recommendations"]:
        for assignment in rec["assignments"]:
            if assignment["player"] == "PlayerA#KR1":
                assert assignment["champion"] == "Viktor", \
                    f"PlayerA should have locked pick Viktor, got {assignment['champion']}"


@pytest.mark.asyncio
async def test_optimize_comp_locked_pick_not_in_pool(client: AsyncClient) -> None:
    """Locked pick with a champion not in the player's pool should still work."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
        ]),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
        ]),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            # Lock a champion that's not in PlayerA's pool
            "locked_picks": {"PlayerA#KR1": "LeeSin"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # PlayerA should still get LeeSin
    for rec in data["recommendations"]:
        for assignment in rec["assignments"]:
            if assignment["player"] == "PlayerA#KR1":
                assert assignment["champion"] == "LeeSin"


@pytest.mark.asyncio
async def test_optimize_comp_bans_and_locked_combined(client: AsyncClient) -> None:
    """Bans and locked picks should work together correctly."""
    players = [
        _make_player_data("PlayerA", "KR1", [
            {"champion_id": 266, "champion_name": "Aatrox", "games": 10, "wins": 7, "win_rate": 0.7, "kda": 3.2, "mastery_points": 100000},
            {"champion_id": 112, "champion_name": "Viktor", "games": 5, "wins": 3, "win_rate": 0.6, "kda": 2.5, "mastery_points": 50000},
            {"champion_id": 64, "champion_name": "LeeSin", "games": 3, "wins": 2, "win_rate": 0.667, "kda": 2.0, "mastery_points": 30000},
        ]),
        _make_player_data("PlayerB", "KR2", [
            {"champion_id": 222, "champion_name": "Jinx", "games": 8, "wins": 5, "win_rate": 0.625, "kda": 4.0, "mastery_points": 80000},
            {"champion_id": 412, "champion_name": "Thresh", "games": 6, "wins": 4, "win_rate": 0.667, "kda": 3.5, "mastery_points": 60000},
        ]),
    ]
    resp = await client.post(
        "/api/optimize-comp",
        json={
            "players": players,
            "banned_champions": ["Aatrox"],
            "locked_picks": {"PlayerA#KR1": "Viktor"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    for rec in data["recommendations"]:
        for assignment in rec["assignments"]:
            # Aatrox should never appear (banned)
            assert assignment["champion"] != "Aatrox"
            # PlayerA must have Viktor (locked)
            if assignment["player"] == "PlayerA#KR1":
                assert assignment["champion"] == "Viktor"
