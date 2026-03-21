from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.classes.action.govern import Govern
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.core.dynasty import Dynasty
from src.classes.official_rank import OFFICIAL_COUNTY, OFFICIAL_NONE
from src.classes.age import Age
from src.classes.root import Root
from src.sim.load.load_game import load_game
from src.sim.save.save_game import save_game
from src.sim.simulator import Simulator
from src.sim.simulator_engine.phases import world as world_phases
from src.systems.time import Month, Year, create_month_stamp
from src.systems.cultivation import Realm
from src.utils.id_generator import get_avatar_id


def _make_avatar(base_world) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name="仕官测试",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = None
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.recalc_effects()
    return avatar


@pytest.mark.asyncio
async def test_govern_finish_grants_reputation_salary_and_promotion(avatar_in_city, base_world):
    avatar_in_city.official_rank = OFFICIAL_NONE
    avatar_in_city.court_reputation = 70
    base_world.dynasty = Dynasty(
        id=1,
        name="秦",
        desc="",
        style_tag="尚法重军",
        official_preference_type="alignment",
        official_preference_value="RIGHTEOUS",
    )

    action = Govern(avatar_in_city, base_world)

    with patch(
        "src.classes.story_event_service.StoryEventService.maybe_create_story",
        new_callable=AsyncMock,
        return_value=None,
    ):
        start_event = action.start()
        finish_events = await action.finish()

    assert "理政" in start_event.content
    assert avatar_in_city.court_reputation == 84
    assert getattr(avatar_in_city.magic_stone, "value", avatar_in_city.magic_stone) == 1040
    assert avatar_in_city.official_rank == OFFICIAL_COUNTY
    assert avatar_in_city.last_governance_month == int(base_world.month_stamp)
    assert avatar_in_city.effects.get("extra_luck", 0) == 2
    assert any("由无品升为县令" in event.content for event in finish_events)


def test_govern_requires_city(dummy_avatar, base_world):
    action = Govern(dummy_avatar, base_world)
    can_start, reason = action.can_start()
    assert can_start is False
    assert "City" in reason or "城市" in reason


def test_phase_update_official_system_decays_and_demotes(dummy_avatar, base_world):
    dummy_avatar.official_rank = OFFICIAL_COUNTY
    dummy_avatar.court_reputation = 80
    dummy_avatar.last_governance_month = int(base_world.month_stamp) - 7
    dummy_avatar.recalc_effects()

    events = world_phases.phase_update_official_system(base_world, [dummy_avatar])

    assert dummy_avatar.court_reputation == 79
    assert dummy_avatar.official_rank == OFFICIAL_NONE
    assert dummy_avatar.effects.get("extra_luck", 0) == 0
    assert len(events) == 1
    assert "降为无品" in events[0].content


def test_save_and_load_preserves_official_fields(base_world, tmp_path):
    avatar = _make_avatar(base_world)
    base_world.avatar_manager.register_avatar(avatar)
    avatar.official_rank = OFFICIAL_COUNTY
    avatar.court_reputation = 123
    avatar.last_governance_month = 5
    avatar.recalc_effects()

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "official_save.json"
    success, _ = save_game(base_world, simulator, existed_sects=[], save_path=save_path)

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    loaded_avatar = next(iter(new_world.avatar_manager.avatars.values()))
    assert loaded_avatar.official_rank == OFFICIAL_COUNTY
    assert loaded_avatar.court_reputation == 123
    assert loaded_avatar.last_governance_month == 5
