import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.orm_models import ChampionAttributeORM
import adapters.outbound.persistence.database as db_module
from domain.models.champion import ChampionAttributes
from domain.ports.repositories.champion_repo import ChampionRepository


def _orm_to_domain(orm: ChampionAttributeORM) -> ChampionAttributes:
    return ChampionAttributes(
        champion_id=orm.champion_id,
        champion_name=orm.champion_name,
        damage_type=orm.damage_type,
        role_tags=json.loads(orm.role_tags_json),
        waveclear=orm.waveclear,
        splitpush=orm.splitpush,
        teamfight=orm.teamfight,
        engage=orm.engage,
        peel=orm.peel,
        poke=orm.poke,
        pick=orm.pick,
        burst=orm.burst,
        primary_lanes=json.loads(orm.primary_lanes_json),
        source=orm.source,
    )


def _domain_to_orm(attrs: ChampionAttributes) -> ChampionAttributeORM:
    return ChampionAttributeORM(
        champion_id=attrs.champion_id,
        champion_name=attrs.champion_name,
        damage_type=attrs.damage_type,
        role_tags_json=json.dumps(attrs.role_tags),
        primary_lanes_json=json.dumps(attrs.primary_lanes),
        waveclear=attrs.waveclear,
        splitpush=attrs.splitpush,
        teamfight=attrs.teamfight,
        engage=attrs.engage,
        peel=attrs.peel,
        poke=attrs.poke,
        pick=attrs.pick,
        burst=attrs.burst,
        source=attrs.source,
        updated_at=datetime.now(timezone.utc),
    )


class ChampionRepositoryImpl(ChampionRepository):
    """SQLModel-based implementation of ChampionRepository."""

    def _get_session_factory(self):
        """Get session factory from module (allows patching in tests)."""
        return db_module.async_session_factory

    async def get_all(self) -> list[ChampionAttributes]:
        async with self._get_session_factory()() as session:
            result = await session.execute(select(ChampionAttributeORM))
            rows = result.scalars().all()
            return [_orm_to_domain(r) for r in rows]

    async def get_by_name(self, name: str) -> ChampionAttributes | None:
        async with self._get_session_factory()() as session:
            result = await session.execute(
                select(ChampionAttributeORM).where(
                    ChampionAttributeORM.champion_name == name
                )
            )
            row = result.scalars().first()
            return _orm_to_domain(row) if row else None

    async def get_by_id(self, champion_id: int) -> ChampionAttributes | None:
        async with self._get_session_factory()() as session:
            result = await session.execute(
                select(ChampionAttributeORM).where(
                    ChampionAttributeORM.champion_id == champion_id
                )
            )
            row = result.scalars().first()
            return _orm_to_domain(row) if row else None

    async def upsert(self, attrs: ChampionAttributes) -> None:
        async with self._get_session_factory()() as session:
            result = await session.execute(
                select(ChampionAttributeORM).where(
                    ChampionAttributeORM.champion_id == attrs.champion_id
                )
            )
            existing = result.scalars().first()

            if existing:
                existing.champion_name = attrs.champion_name
                existing.damage_type = attrs.damage_type
                existing.role_tags_json = json.dumps(attrs.role_tags)
                existing.primary_lanes_json = json.dumps(attrs.primary_lanes)
                existing.waveclear = attrs.waveclear
                existing.splitpush = attrs.splitpush
                existing.teamfight = attrs.teamfight
                existing.engage = attrs.engage
                existing.peel = attrs.peel
                existing.poke = attrs.poke
                existing.pick = attrs.pick
                existing.burst = attrs.burst
                existing.source = attrs.source
                existing.updated_at = datetime.now(timezone.utc)
                session.add(existing)
            else:
                orm = _domain_to_orm(attrs)
                session.add(orm)

            await session.commit()

    async def upsert_many(self, attrs_list: list[ChampionAttributes]) -> None:
        async with self._get_session_factory()() as session:
            for attrs in attrs_list:
                result = await session.execute(
                    select(ChampionAttributeORM).where(
                        ChampionAttributeORM.champion_id == attrs.champion_id
                    )
                )
                existing = result.scalars().first()

                if existing:
                    existing.champion_name = attrs.champion_name
                    existing.damage_type = attrs.damage_type
                    existing.role_tags_json = json.dumps(attrs.role_tags)
                    existing.waveclear = attrs.waveclear
                    existing.splitpush = attrs.splitpush
                    existing.teamfight = attrs.teamfight
                    existing.engage = attrs.engage
                    existing.peel = attrs.peel
                    existing.poke = attrs.poke
                    existing.pick = attrs.pick
                    existing.burst = attrs.burst
                    existing.source = attrs.source
                    existing.updated_at = datetime.now(timezone.utc)
                    session.add(existing)
                else:
                    orm = _domain_to_orm(attrs)
                    session.add(orm)

            await session.commit()
