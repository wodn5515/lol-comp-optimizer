"""E2E test fixtures — standalone setup with mocked external services."""

import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tests.integration.conftest import MockRiotApi, MockDataDragon


@pytest.fixture
def mock_riot_api() -> MockRiotApi:
    return MockRiotApi()


@pytest.fixture
def mock_ddragon() -> MockDataDragon:
    return MockDataDragon()


@pytest_asyncio.fixture
async def client(mock_riot_api: MockRiotApi, mock_ddragon: MockDataDragon):
    """Create a test client with mocked external services and in-memory DB.

    Ensures `import main` happens BEFORE init_router so that main.py's
    top-level init_router call (with real services) is overwritten by mocks.
    """
    # Create in-memory async engine
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False,
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
    import main as main_module  # noqa: F401

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
