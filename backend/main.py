import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from adapters.outbound.persistence.database import init_db
from adapters.outbound.persistence.champion_repo_impl import ChampionRepositoryImpl
from adapters.outbound.external.riot_api_client import RiotApiClient, SlidingWindowRateLimiter
from adapters.outbound.external.ddragon_client import DataDragonClient
from domain.services.champion_data_service import ChampionDataService
from domain.services.player_analysis_service import PlayerAnalysisService
from domain.services.lane_optimizer_service import LaneOptimizerService
from domain.services.comp_optimizer_service import CompOptimizerService
from domain.models.champion import ChampionAttributes
from adapters.inbound.api import champion_router, optimize_router


# Create adapters
champion_repo = ChampionRepositoryImpl()
rate_limiter = SlidingWindowRateLimiter()
riot_api_client = RiotApiClient(rate_limiter)
ddragon_client = DataDragonClient()

# Create services (DI)
champion_data_service = ChampionDataService(champion_repo)
player_analysis_service = PlayerAnalysisService()
lane_optimizer_service = LaneOptimizerService()
comp_optimizer_service = CompOptimizerService()


async def seed_champions_if_empty() -> None:
    """Load champion_attributes.json and seed DB if empty."""
    existing = await champion_repo.get_all()
    if existing:
        return

    json_path = os.path.join(os.path.dirname(__file__), "champion_attributes.json")
    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    attrs_list: list[ChampionAttributes] = []
    for name, attrs_dict in data.items():
        attrs_list.append(
            ChampionAttributes(
                champion_id=attrs_dict["champion_id"],
                champion_name=name,
                champion_name_ko=attrs_dict.get("champion_name_ko", ""),
                damage_type=attrs_dict["damage_type"],
                role_tags=attrs_dict["role_tags"],
                primary_lanes=attrs_dict.get("primary_lanes", ["TOP", "MID"]),
                waveclear=attrs_dict["waveclear"],
                splitpush=attrs_dict["splitpush"],
                teamfight=attrs_dict["teamfight"],
                engage=attrs_dict["engage"],
                peel=attrs_dict["peel"],
                poke=attrs_dict.get("poke", 3),
                pick=attrs_dict.get("pick", 3),
                burst=attrs_dict.get("burst", 3),
                source="MANUAL",
            )
        )

    await champion_repo.upsert_many(attrs_list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await seed_champions_if_empty()
    yield
    # Shutdown
    await riot_api_client.close()
    await ddragon_client.close()


app = FastAPI(
    title="LoL Comp Optimizer",
    description="League of Legends team composition optimizer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire up routers with DI
champion_router.init_router(champion_data_service)
optimize_router.init_router(
    riot=riot_api_client,
    dd=ddragon_client,
    pa=player_analysis_service,
    lo=lane_optimizer_service,
    co=comp_optimizer_service,
    cd=champion_data_service,
)

app.include_router(champion_router.router)
app.include_router(optimize_router.router)
