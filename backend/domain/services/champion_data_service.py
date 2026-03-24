from domain.models.champion import ChampionAttributes
from domain.ports.repositories.champion_repo import ChampionRepository


# Default attribute mappings based on Data Dragon tags
_TAG_DEFAULTS: dict[str, dict] = {
    "Tank": {
        "damage_type": "AP",
        "role_tags": ["TANK"],
        "primary_lanes": ["TOP", "SUP"],
        "waveclear": 3,
        "splitpush": 2,
        "teamfight": 3,
        "engage": 3,
        "peel": 2,
        "poke": 1,
        "pick": 1,
        "burst": 1,
    },
    "Assassin": {
        "damage_type": "AD",
        "role_tags": ["ASSASSIN"],
        "primary_lanes": ["MID", "JG"],
        "waveclear": 2,
        "splitpush": 3,
        "teamfight": 2,
        "engage": 2,
        "peel": 1,
        "poke": 2,
        "pick": 4,
        "burst": 5,
    },
    "Mage": {
        "damage_type": "AP",
        "role_tags": ["MAGE"],
        "primary_lanes": ["MID"],
        "waveclear": 4,
        "splitpush": 2,
        "teamfight": 3,
        "engage": 2,
        "peel": 2,
        "poke": 4,
        "pick": 2,
        "burst": 3,
    },
    "Marksman": {
        "damage_type": "AD",
        "role_tags": ["MARKSMAN"],
        "primary_lanes": ["ADC"],
        "waveclear": 3,
        "splitpush": 3,
        "teamfight": 3,
        "engage": 1,
        "peel": 1,
        "poke": 3,
        "pick": 1,
        "burst": 2,
    },
    "Support": {
        "damage_type": "AP",
        "role_tags": ["SUPPORT"],
        "primary_lanes": ["SUP"],
        "waveclear": 2,
        "splitpush": 1,
        "teamfight": 2,
        "engage": 3,
        "peel": 4,
        "poke": 2,
        "pick": 2,
        "burst": 1,
    },
    "Fighter": {
        "damage_type": "AD",
        "role_tags": ["BRUISER"],
        "primary_lanes": ["TOP"],
        "waveclear": 3,
        "splitpush": 3,
        "teamfight": 3,
        "engage": 3,
        "peel": 1,
        "poke": 1,
        "pick": 2,
        "burst": 3,
    },
}


class ChampionDataService:
    def __init__(self, champion_repo: ChampionRepository) -> None:
        self._repo = champion_repo

    async def get_attributes(self, champion_name: str) -> ChampionAttributes | None:
        """Get champion attributes from the repository (manual data)."""
        return await self._repo.get_by_name(champion_name)

    async def get_attributes_by_id(self, champion_id: int) -> ChampionAttributes | None:
        """Get champion attributes by Riot champion ID."""
        return await self._repo.get_by_id(champion_id)

    async def get_all(self) -> list[ChampionAttributes]:
        """Get all champion attributes from the repository."""
        return await self._repo.get_all()

    def get_attributes_with_fallback(
        self,
        champion_name: str,
        ddragon_tags: list[str],
        champion_id: int = 0,
        existing: ChampionAttributes | None = None,
    ) -> ChampionAttributes:
        """Return existing manual attributes, or generate defaults from Data Dragon tags.

        Args:
            champion_name: Champion name (e.g. "Aatrox")
            ddragon_tags: Tags from Data Dragon (e.g. ["Fighter", "Tank"])
            champion_id: Riot champion ID
            existing: Previously loaded attributes from repo, if any

        Returns:
            ChampionAttributes with either manual or auto-generated data.
        """
        if existing is not None:
            return existing

        # Generate defaults from the first recognized tag
        attrs = ChampionAttributes(
            champion_id=champion_id,
            champion_name=champion_name,
            source="AUTO",
        )

        primary_tag = ddragon_tags[0] if ddragon_tags else "Fighter"
        defaults = _TAG_DEFAULTS.get(primary_tag, _TAG_DEFAULTS["Fighter"])

        attrs.damage_type = defaults["damage_type"]
        attrs.role_tags = list(defaults["role_tags"])
        attrs.primary_lanes = list(defaults["primary_lanes"])
        attrs.waveclear = defaults["waveclear"]
        attrs.splitpush = defaults["splitpush"]
        attrs.teamfight = defaults["teamfight"]
        attrs.engage = defaults["engage"]
        attrs.peel = defaults["peel"]
        attrs.poke = defaults["poke"]
        attrs.pick = defaults["pick"]
        attrs.burst = defaults["burst"]

        # If there's a secondary tag, merge role_tags
        if len(ddragon_tags) > 1:
            secondary_tag = ddragon_tags[1]
            secondary_defaults = _TAG_DEFAULTS.get(secondary_tag)
            if secondary_defaults:
                for tag in secondary_defaults["role_tags"]:
                    if tag not in attrs.role_tags:
                        attrs.role_tags.append(tag)

        return attrs
