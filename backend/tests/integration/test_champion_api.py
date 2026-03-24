import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_all_champions(client: AsyncClient) -> None:
    resp = await client.get("/api/champions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Check structure
    champ = data[0]
    assert "champion_id" in champ
    assert "champion_name" in champ
    assert "damage_type" in champ
    assert "role_tags" in champ
    assert "waveclear" in champ
    assert "splitpush" in champ
    assert "teamfight" in champ
    assert "engage" in champ
    assert "peel" in champ


@pytest.mark.asyncio
async def test_get_champion_by_id(client: AsyncClient) -> None:
    # Aatrox was seeded in conftest
    resp = await client.get("/api/champions/266")
    assert resp.status_code == 200
    data = resp.json()
    assert data["champion_name"] == "Aatrox"
    assert data["damage_type"] == "AD"
    assert "BRUISER" in data["role_tags"]


@pytest.mark.asyncio
async def test_get_champion_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/champions/99999")
    assert resp.status_code == 404
