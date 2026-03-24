from abc import ABC, abstractmethod
from domain.models.champion import ChampionAttributes


class ChampionRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[ChampionAttributes]:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> ChampionAttributes | None:
        ...

    @abstractmethod
    async def get_by_id(self, champion_id: int) -> ChampionAttributes | None:
        ...

    @abstractmethod
    async def upsert(self, attrs: ChampionAttributes) -> None:
        ...

    @abstractmethod
    async def upsert_many(self, attrs_list: list[ChampionAttributes]) -> None:
        ...
