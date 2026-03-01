import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.classes.gathering.tournament import Tournament
from src.systems.time import Month, Year, create_month_stamp
from src.systems.cultivation import Realm
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.utils.id_generator import get_avatar_id


def create_mock_avatar(base_world, name, realm, power):
    av = Avatar(
        world=base_world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, realm),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS
    )
    av.cultivation_progress.realm = realm
    av.weapon = MagicMock()
    av.weapon.get_detailed_info.return_value = "测试武器"
    av.weapon_proficiency = 0.0
    av.personas = []
    av.technique = None
    
    # Avoid real calculation overhead
    av.recalc_effects = MagicMock()
    
    # We will mock get_base_strength in the test instead of setting effects
    av._mock_power = power
    
    return av


@pytest.mark.asyncio
async def test_tournament_is_start(base_world):
    tournament = Tournament()
    base_world.start_year = 1
    
    # Not January
    base_world.month_stamp = create_month_stamp(Year(2), Month.FEBRUARY)
    assert not tournament.is_start(base_world)
    
    # January, year 1 (before start_year + 1)
    base_world.month_stamp = create_month_stamp(Year(1), Month.JANUARY)
    assert not tournament.is_start(base_world)
    
    # January, year 2 (first tournament)
    base_world.month_stamp = create_month_stamp(Year(2), Month.JANUARY)
    assert tournament.is_start(base_world)
    
    # January, year 11 (not a decade from year 2)
    base_world.month_stamp = create_month_stamp(Year(11), Month.JANUARY)
    assert not tournament.is_start(base_world)
    
    # January, year 12 (second tournament)
    base_world.month_stamp = create_month_stamp(Year(12), Month.JANUARY)
    assert tournament.is_start(base_world)


@pytest.mark.asyncio
@patch("src.classes.gathering.tournament.get_base_strength")
async def test_tournament_execute_insufficient_participants(mock_get_strength, base_world):
    mock_get_strength.side_effect = lambda av: getattr(av, "_mock_power", 0)
    tournament = Tournament()
    
    # Less than 4 avatars in human list
    av1 = create_mock_avatar(base_world, "H1", Realm.Foundation_Establishment, 100)
    av2 = create_mock_avatar(base_world, "H2", Realm.Foundation_Establishment, 90)
    av3 = create_mock_avatar(base_world, "H3", Realm.Foundation_Establishment, 80)
    
    base_world.avatar_manager = MagicMock()
    base_world.avatar_manager.get_living_avatars.return_value = [av1, av2, av3]
    base_world.ranking_manager = MagicMock()
    
    events = await tournament.execute(base_world)
    
    from src.i18n import t
    # Should not run any list, but instead generate a cancellation event
    assert len(events) == 1
    assert t("tournament_cancelled_due_to_insufficient_participants") in events[0].content
    assert events[0].is_major is True


@pytest.mark.asyncio
@patch("src.classes.gathering.tournament.get_base_strength")
async def test_tournament_execute_human_list(mock_get_strength, base_world, mock_llm_managers):
    mock_get_strength.side_effect = lambda av: getattr(av, "_mock_power", 0)
    tournament = Tournament()
    
    # 5 avatars in human list (Foundation_Establishment)
    # The 5th should be ignored
    av1 = create_mock_avatar(base_world, "H1", Realm.Foundation_Establishment, 100)
    av2 = create_mock_avatar(base_world, "H2", Realm.Foundation_Establishment, 90)
    av3 = create_mock_avatar(base_world, "H3", Realm.Foundation_Establishment, 80)
    av4 = create_mock_avatar(base_world, "H4", Realm.Foundation_Establishment, 70)
    av5 = create_mock_avatar(base_world, "H5", Realm.Foundation_Establishment, 60)
    
    base_world.avatar_manager = MagicMock()
    base_world.avatar_manager.get_living_avatars.return_value = [av1, av2, av3, av4, av5]
    base_world.ranking_manager = MagicMock()
    del base_world.ranking_manager.tournament_info
    base_world.start_year = 1
    base_world.month_stamp = create_month_stamp(Year(2), Month.JANUARY)
    
    # Execute tournament
    events = await tournament.execute(base_world)
    
    # Should have events:
    # 1 start event
    # 2 semi-finals
    # 1 final
    # 1 end event
    # 1 story event
    assert len(events) == 6
    
    # Check that H5 is not in the start event
    start_event = events[0]
    assert "H1" in start_event.content
    assert "H2" in start_event.content
    assert "H3" in start_event.content
    assert "H4" in start_event.content
    assert "H5" not in start_event.content
    
    # Check tournament_info was populated
    tournament_info = base_world.ranking_manager.tournament_info
    assert tournament_info["next_year"] == 12
    assert tournament_info["human_first"] is not None
    assert tournament_info["earth_first"] is None
    assert tournament_info["heaven_first"] is None
    
    # Winner should get 2000 spirit stones
    winner_name = tournament_info["human_first"]["name"]
    winner = next(av for av in [av1, av2, av3, av4] if av.name == winner_name)
    assert winner.magic_stone.value == 2000
    
    # Winner should have temporary effect
    assert len(winner.temporary_effects) == 1
    assert winner.temporary_effects[0]["source"] == "tournament_human"
    
    # Story should be generated
    mock_llm_managers["gathering_story"].assert_called_once()


def test_tournament_registered():
    from src.classes.gathering.gathering import GatheringManager
    manager = GatheringManager()
    assert any(isinstance(g, Tournament) for g in manager.gatherings)
