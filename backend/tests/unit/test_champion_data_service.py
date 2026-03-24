import pytest
from unittest.mock import AsyncMock

from domain.models.champion import ChampionAttributes
from domain.services.champion_data_service import ChampionDataService


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_repo: AsyncMock) -> ChampionDataService:
    return ChampionDataService(mock_repo)


class TestGetAttributes:
    @pytest.mark.asyncio
    async def test_manual_champion_returns_attributes(self, service: ChampionDataService, mock_repo: AsyncMock) -> None:
        """Spec section 3: Manually entered champions return accurate attributes."""
        aatrox = ChampionAttributes(
            champion_id=266,
            champion_name="Aatrox",
            damage_type="AD",
            role_tags=["BRUISER"],
            waveclear=4,
            splitpush=3,
            teamfight=4,
            engage=3,
            peel=1,
            source="MANUAL",
        )
        mock_repo.get_by_name.return_value = aatrox

        result = await service.get_attributes("Aatrox")
        assert result is not None
        assert result.damage_type == "AD"
        assert "BRUISER" in result.role_tags
        assert result.waveclear == 4
        assert result.source == "MANUAL"

    @pytest.mark.asyncio
    async def test_unknown_champion_returns_none(self, service: ChampionDataService) -> None:
        result = await service.get_attributes("NonexistentChamp")
        assert result is None


class TestGetAttributesWithFallback:
    def test_existing_attrs_returned(self, service: ChampionDataService) -> None:
        existing = ChampionAttributes(
            champion_id=266,
            champion_name="Aatrox",
            damage_type="AD",
            role_tags=["BRUISER"],
            source="MANUAL",
        )
        result = service.get_attributes_with_fallback(
            champion_name="Aatrox",
            ddragon_tags=["Fighter", "Tank"],
            existing=existing,
        )
        assert result.source == "MANUAL"
        assert result.damage_type == "AD"

    def test_unknown_champion_gets_defaults_from_tags(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Champs without manual data get defaults from DD tags."""
        result = service.get_attributes_with_fallback(
            champion_name="NewChamp",
            ddragon_tags=["Mage", "Support"],
            champion_id=999,
        )
        assert result.damage_type == "AP"
        assert result.source == "AUTO"
        assert "MAGE" in result.role_tags
        assert "SUPPORT" in result.role_tags

    def test_tank_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Tank tag -> waveclear=3, teamfight=3."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Tank"],
        )
        assert result.waveclear == 3
        assert result.teamfight == 3
        assert result.damage_type == "AP"
        assert "TANK" in result.role_tags
        assert result.poke == 1
        assert result.pick == 1
        assert result.burst == 1

    def test_assassin_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Assassin tag -> splitpush=3, teamfight=2."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Assassin"],
        )
        assert result.splitpush == 3
        assert result.teamfight == 2
        assert result.damage_type == "AD"
        assert "ASSASSIN" in result.role_tags
        assert result.poke == 2
        assert result.pick == 4
        assert result.burst == 5

    def test_mage_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Mage tag -> damage_type=AP, waveclear=4."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Mage"],
        )
        assert result.damage_type == "AP"
        assert result.waveclear == 4
        assert "MAGE" in result.role_tags
        assert result.poke == 4
        assert result.pick == 2
        assert result.burst == 3

    def test_marksman_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Marksman tag -> damage_type=AD, teamfight=3."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Marksman"],
        )
        assert result.damage_type == "AD"
        assert result.teamfight == 3
        assert "MARKSMAN" in result.role_tags
        assert result.poke == 3
        assert result.pick == 1
        assert result.burst == 2

    def test_support_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Support tag -> peel=4, engage=3."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Support"],
        )
        assert result.peel == 4
        assert result.engage == 3
        assert "SUPPORT" in result.role_tags
        assert result.poke == 2
        assert result.pick == 2
        assert result.burst == 1

    def test_fighter_tag_defaults(self, service: ChampionDataService) -> None:
        """Spec section 3-2: Fighter -> BRUISER, waveclear=3, teamfight=3, splitpush=3."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Fighter"],
        )
        assert result.damage_type == "AD"
        assert result.waveclear == 3
        assert result.teamfight == 3
        assert result.splitpush == 3
        assert "BRUISER" in result.role_tags
        assert result.poke == 1
        assert result.pick == 2
        assert result.burst == 3

    def test_secondary_tag_merged(self, service: ChampionDataService) -> None:
        """Secondary DD tag should add role_tags."""
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=["Fighter", "Tank"],
        )
        assert "BRUISER" in result.role_tags
        assert "TANK" in result.role_tags

    def test_empty_tags_defaults_to_fighter(self, service: ChampionDataService) -> None:
        result = service.get_attributes_with_fallback(
            champion_name="Unknown",
            ddragon_tags=[],
        )
        assert result.damage_type == "AD"
        assert "BRUISER" in result.role_tags
