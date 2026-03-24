import httpx

from domain.ports.external.ddragon_port import DataDragonPort

DDRAGON_BASE = "https://ddragon.leagueoflegends.com"


class DataDragonClient(DataDragonPort):
    """Data Dragon HTTP client for champion static data."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=15.0)
        self._cached_version: str | None = None
        self._cached_champions: dict | None = None

    async def get_latest_version(self) -> str:
        if self._cached_version:
            return self._cached_version
        resp = await self._client.get(f"{DDRAGON_BASE}/api/versions.json")
        resp.raise_for_status()
        versions = resp.json()
        self._cached_version = versions[0]
        return self._cached_version

    async def get_all_champions(self) -> dict:
        """Returns dict of champion_key (str number) -> champion info dict.

        Each value has: {"name": str, "id": str, "key": str, "tags": list[str]}
        """
        if self._cached_champions:
            return self._cached_champions

        version = await self.get_latest_version()
        resp = await self._client.get(
            f"{DDRAGON_BASE}/cdn/{version}/data/ko_KR/champion.json"
        )
        resp.raise_for_status()
        data = resp.json()["data"]

        result: dict = {}
        for champ_id, champ_data in data.items():
            key = champ_data["key"]  # This is the numeric champion ID as string
            result[key] = {
                "name": champ_data["name"],
                "id": champ_data["id"],  # String ID like "Aatrox"
                "key": key,
                "tags": champ_data.get("tags", []),
            }

        self._cached_champions = result
        return result

    async def close(self) -> None:
        await self._client.aclose()
