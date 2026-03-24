from abc import ABC, abstractmethod


class DataDragonPort(ABC):
    @abstractmethod
    async def get_all_champions(self) -> dict:
        """Returns dict of champion_key -> {"name": ..., "id": ..., "key": ..., "tags": [...]}"""
        ...

    @abstractmethod
    async def get_latest_version(self) -> str:
        ...
