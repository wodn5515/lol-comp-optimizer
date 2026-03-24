import os
import sys

import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from domain.ports.external.riot_api_port import RiotApiPort
from domain.ports.external.ddragon_port import DataDragonPort


class MockRiotApi(RiotApiPort):
    """Mock Riot API for integration tests."""

    def __init__(self) -> None:
        self._not_found: set[str] = set()

    def set_not_found(self, game_name: str, tag_line: str) -> None:
        self._not_found.add(f"{game_name}#{tag_line}")

    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str, api_key: str
    ) -> dict | None:
        key = f"{game_name}#{tag_line}"
        if key in self._not_found:
            return None
        return {
            "puuid": f"puuid-{game_name}",
            "gameName": game_name,
            "tagLine": tag_line,
        }

    async def get_summoner_by_puuid(
        self, puuid: str, api_key: str
    ) -> dict | None:
        return {
            "id": f"summoner-{puuid}",
            "puuid": puuid,
            "profileIconId": 1234,
            "summonerLevel": 100,
        }

    async def get_league_entries(
        self, summoner_id: str, api_key: str
    ) -> list[dict]:
        return [
            {
                "queueType": "RANKED_SOLO_5x5",
                "tier": "GOLD",
                "rank": "II",
                "leaguePoints": 50,
                "wins": 100,
                "losses": 90,
            }
        ]

    async def get_match_ids(
        self, puuid: str, count: int, queue: int | None, api_key: str,
        match_type: str | None = None,
        start_time: int | None = None,
    ) -> list[str]:
        return [f"KR_match_{puuid}_{i}" for i in range(min(count, 3))]

    async def get_match_detail(
        self, match_id: str, api_key: str
    ) -> dict | None:
        parts = match_id.split("_")
        puuid = "_".join(parts[2:-1]) if len(parts) > 3 else "unknown"
        match_index = int(parts[-1]) if parts[-1].isdigit() else 0

        lanes = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
        champions = [
            (266, "Aatrox"),
            (64, "LeeSin"),
            (112, "Viktor"),
            (222, "Jinx"),
            (412, "Thresh"),
        ]
        # Summoner spells: Smite (11) for jungle, Flash (4) + others for rest
        # Format: (spell1, spell2)
        spells = [
            (4, 14),   # TOP: Flash + Ignite
            (11, 4),   # JUNGLE: Smite + Flash
            (4, 14),   # MIDDLE: Flash + Ignite
            (4, 7),    # BOTTOM: Flash + Heal
            (4, 3),    # UTILITY: Flash + Exhaust
        ]

        lane = lanes[match_index % 5]
        champ_id, champ_name = champions[match_index % 5]
        spell1, spell2 = spells[match_index % 5]

        return {
            "info": {
                "queueId": 420,
                "gameDuration": 1800,
                "participants": [
                    {
                        "puuid": puuid,
                        "teamPosition": lane,
                        "championId": champ_id,
                        "championName": champ_name,
                        "win": match_index % 2 == 0,
                        "kills": 5 + match_index,
                        "deaths": 3,
                        "assists": 7,
                        "totalMinionsKilled": 150,
                        "neutralMinionsKilled": 20,
                        "summoner1Id": spell1,
                        "summoner2Id": spell2,
                    }
                ],
            }
        }

    async def get_champion_masteries(
        self, puuid: str, top: int, api_key: str
    ) -> list[dict]:
        return [
            {"championId": 266, "championPoints": 100000},
            {"championId": 64, "championPoints": 80000},
            {"championId": 112, "championPoints": 60000},
            {"championId": 222, "championPoints": 40000},
            {"championId": 412, "championPoints": 20000},
        ]


class MockDataDragon(DataDragonPort):
    """Mock Data Dragon for integration tests."""

    async def get_latest_version(self) -> str:
        return "14.10.1"

    async def get_all_champions(self) -> dict:
        return {
            "266": {"name": "아트록스", "id": "Aatrox", "key": "266", "tags": ["Fighter", "Tank"]},
            "64": {"name": "리 신", "id": "LeeSin", "key": "64", "tags": ["Fighter", "Assassin"]},
            "112": {"name": "빅토르", "id": "Viktor", "key": "112", "tags": ["Mage"]},
            "222": {"name": "징크스", "id": "Jinx", "key": "222", "tags": ["Marksman"]},
            "412": {"name": "쓰레쉬", "id": "Thresh", "key": "412", "tags": ["Support", "Fighter"]},
        }


@pytest.fixture
def mock_riot_api() -> MockRiotApi:
    return MockRiotApi()


@pytest.fixture
def mock_ddragon() -> MockDataDragon:
    return MockDataDragon()


@pytest_asyncio.fixture
async def client(mock_riot_api: MockRiotApi, mock_ddragon: MockDataDragon):
    """Create a test client with mocked external services and in-memory DB."""
    import json

    # Create in-memory async engine
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Patch the database module to use our test engine/session
    import adapters.outbound.persistence.database as db_module
    original_engine = db_module.async_engine
    original_session_factory = db_module.async_session_factory

    db_module.async_engine = test_engine
    db_module.async_session_factory = test_session_factory

    # Import ORM models and create tables
    from adapters.outbound.persistence.orm_models import ChampionAttributeORM  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Import main FIRST so its top-level code (including init_router with
    # real services) runs before we overwrite with mocks.
    import main as main_module

    # Create services with mocks
    from adapters.outbound.persistence.champion_repo_impl import ChampionRepositoryImpl
    from domain.services.champion_data_service import ChampionDataService
    from domain.services.player_analysis_service import PlayerAnalysisService
    from domain.services.lane_optimizer_service import LaneOptimizerService
    from domain.services.comp_optimizer_service import CompOptimizerService
    from domain.models.champion import ChampionAttributes

    champion_repo = ChampionRepositoryImpl()
    champion_data_svc = ChampionDataService(champion_repo)
    player_analysis_svc = PlayerAnalysisService()
    lane_optimizer_svc = LaneOptimizerService()
    comp_optimizer_svc = CompOptimizerService()

    # Seed test champion data
    test_champions = [
        ChampionAttributes(champion_id=266, champion_name="Aatrox", damage_type="AD", role_tags=["BRUISER"], primary_lanes=["TOP"], waveclear=4, splitpush=3, teamfight=4, engage=3, peel=1, poke=1, pick=2, burst=3),
        ChampionAttributes(champion_id=64, champion_name="LeeSin", damage_type="AD", role_tags=["BRUISER", "ASSASSIN"], primary_lanes=["JG"], waveclear=3, splitpush=2, teamfight=3, engage=4, peel=2, poke=1, pick=3, burst=4),
        ChampionAttributes(champion_id=112, champion_name="Viktor", damage_type="AP", role_tags=["MAGE"], primary_lanes=["MID"], waveclear=5, splitpush=2, teamfight=4, engage=1, peel=1, poke=4, pick=2, burst=3),
        ChampionAttributes(champion_id=222, champion_name="Jinx", damage_type="AD", role_tags=["MARKSMAN"], primary_lanes=["ADC"], waveclear=4, splitpush=3, teamfight=4, engage=1, peel=1, poke=3, pick=1, burst=2),
        ChampionAttributes(champion_id=412, champion_name="Thresh", damage_type="AP", role_tags=["SUPPORT", "TANK"], primary_lanes=["SUP"], waveclear=1, splitpush=1, teamfight=4, engage=4, peel=4, poke=2, pick=2, burst=1),
    ]
    await champion_repo.upsert_many(test_champions)

    # Wire up routers with mock services AFTER main import
    from adapters.inbound.api import optimize_router, champion_router

    optimize_router.init_router(
        riot=mock_riot_api,
        dd=mock_ddragon,
        pa=player_analysis_svc,
        lo=lane_optimizer_svc,
        co=comp_optimizer_svc,
        cd=champion_data_svc,
    )
    champion_router.init_router(champion_data_svc)

    transport = ASGITransport(app=main_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore original
    db_module.async_engine = original_engine
    db_module.async_session_factory = original_session_factory

    await test_engine.dispose()
