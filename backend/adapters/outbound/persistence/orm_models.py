import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class ChampionAttributeORM(SQLModel, table=True):
    __tablename__ = "champion_attribute"

    id: Optional[int] = Field(default=None, primary_key=True)
    champion_id: int = Field(index=True, unique=True)
    champion_name: str = Field(index=True)
    champion_name_ko: str = Field(default="")
    damage_type: str = Field(default="AD")
    role_tags_json: str = Field(default='[]')  # JSON string of list[str]
    primary_lanes_json: str = Field(default='[]')  # JSON string of list[str]
    waveclear: int = Field(default=3)
    splitpush: int = Field(default=3)
    teamfight: int = Field(default=3)
    engage: int = Field(default=3)
    peel: int = Field(default=1)
    poke: int = Field(default=3)
    pick: int = Field(default=3)
    burst: int = Field(default=3)
    play_tips: str = Field(default="")
    meta_tier_json: str = Field(default='{}')  # JSON string of dict[str, str]
    source: str = Field(default="MANUAL")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def role_tags(self) -> list[str]:
        return json.loads(self.role_tags_json)

    @role_tags.setter
    def role_tags(self, value: list[str]) -> None:
        self.role_tags_json = json.dumps(value)

    @property
    def primary_lanes(self) -> list[str]:
        return json.loads(self.primary_lanes_json)

    @primary_lanes.setter
    def primary_lanes(self, value: list[str]) -> None:
        self.primary_lanes_json = json.dumps(value)

    @property
    def meta_tier(self) -> dict[str, str]:
        return json.loads(self.meta_tier_json)

    @meta_tier.setter
    def meta_tier(self, value: dict[str, str]) -> None:
        self.meta_tier_json = json.dumps(value)
