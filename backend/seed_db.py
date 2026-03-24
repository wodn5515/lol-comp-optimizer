"""Script to seed champion attributes from JSON into the database.

Usage:
    cd backend
    python seed_db.py
"""

import asyncio
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from adapters.outbound.persistence.database import init_db
from adapters.outbound.persistence.champion_repo_impl import ChampionRepositoryImpl
from domain.models.champion import ChampionAttributes


async def seed() -> None:
    await init_db()

    repo = ChampionRepositoryImpl()

    json_path = os.path.join(os.path.dirname(__file__), "champion_attributes.json")
    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    attrs_list: list[ChampionAttributes] = []
    for name, attrs_dict in data.items():
        attrs_list.append(
            ChampionAttributes(
                champion_id=attrs_dict["champion_id"],
                champion_name=name,
                damage_type=attrs_dict["damage_type"],
                role_tags=attrs_dict["role_tags"],
                waveclear=attrs_dict["waveclear"],
                splitpush=attrs_dict["splitpush"],
                teamfight=attrs_dict["teamfight"],
                engage=attrs_dict["engage"],
                peel=attrs_dict["peel"],
                source="MANUAL",
            )
        )

    await repo.upsert_many(attrs_list)
    print(f"Seeded {len(attrs_list)} champion attributes into the database.")


if __name__ == "__main__":
    asyncio.run(seed())
