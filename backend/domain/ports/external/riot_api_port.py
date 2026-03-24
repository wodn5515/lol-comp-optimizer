from abc import ABC, abstractmethod


class RiotApiPort(ABC):
    @abstractmethod
    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str, api_key: str
    ) -> dict | None:
        ...

    @abstractmethod
    async def get_summoner_by_puuid(
        self, puuid: str, api_key: str
    ) -> dict | None:
        ...

    @abstractmethod
    async def get_league_entries(
        self, summoner_id: str, api_key: str
    ) -> list[dict]:
        ...

    @abstractmethod
    async def get_match_ids(
        self, puuid: str, count: int, queue: int | None, api_key: str,
        match_type: str | None = None,
        start_time: int | None = None,
    ) -> list[str]:
        ...

    @abstractmethod
    async def get_match_detail(
        self, match_id: str, api_key: str
    ) -> dict | None:
        ...

    @abstractmethod
    async def get_champion_masteries(
        self, puuid: str, top: int, api_key: str
    ) -> list[dict]:
        ...
