from fastapi import APIRouter, HTTPException

from domain.services.champion_data_service import ChampionDataService

router = APIRouter(prefix="/api", tags=["champions"])

# Will be set by main.py during DI assembly
champion_data_service: ChampionDataService | None = None


def init_router(service: ChampionDataService) -> None:
    global champion_data_service
    champion_data_service = service


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@router.get("/champions")
async def get_all_champions() -> list[dict]:
    """Return all champion attributes."""
    if champion_data_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    champions = await champion_data_service.get_all()
    return [
        {
            "champion_id": c.champion_id,
            "champion_name": c.champion_name,
            "champion_name_ko": c.champion_name_ko,
            "damage_type": c.damage_type,
            "role_tags": c.role_tags,
            "waveclear": c.waveclear,
            "splitpush": c.splitpush,
            "teamfight": c.teamfight,
            "engage": c.engage,
            "peel": c.peel,
            "source": c.source,
        }
        for c in champions
    ]


@router.get("/champions/{champion_id}")
async def get_champion(champion_id: int) -> dict:
    """Return single champion attributes by Riot champion ID."""
    if champion_data_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    champion = await champion_data_service.get_attributes_by_id(champion_id)
    if champion is None:
        raise HTTPException(status_code=404, detail="챔피언을 찾을 수 없습니다")

    return {
        "champion_id": champion.champion_id,
        "champion_name": champion.champion_name,
        "champion_name_ko": champion.champion_name_ko,
        "damage_type": champion.damage_type,
        "role_tags": champion.role_tags,
        "waveclear": champion.waveclear,
        "splitpush": champion.splitpush,
        "teamfight": champion.teamfight,
        "engage": champion.engage,
        "peel": champion.peel,
        "source": champion.source,
    }
