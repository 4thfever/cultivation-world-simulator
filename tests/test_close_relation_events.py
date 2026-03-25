import pytest
from unittest.mock import patch

from src.classes.age import Age
from src.classes.event import Event
from src.classes.core.avatar import Avatar, Gender
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.systems.cultivation import Realm
from src.systems.time import Year, Month, create_month_stamp
from src.utils.id_generator import get_avatar_id
from src.sim.simulator_engine.context import SimulationStepContext
from src.sim.simulator_engine.finalizer import finalize_step
from src.systems.battle import handle_battle_finish
from src.classes.mutual_action.confess import Confess
from src.systems.fortune import try_trigger_fortune


def _make_avatar(world, name: str, gender: Gender = Gender.MALE) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=gender,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = None
    avatar.recalc_effects()
    return avatar


def test_major_event_propagates_to_close_relation(base_world):
    parent = _make_avatar(base_world, "Parent")
    child = _make_avatar(base_world, "Child")
    child.acknowledge_parent(parent)
    base_world.avatar_manager.register_avatar(parent)
    base_world.avatar_manager.register_avatar(child)

    event = Event(
        month_stamp=base_world.month_stamp,
        content="Child successfully broke through.",
        related_avatars=[child.id],
        is_major=True,
        event_type="cultivation_major",
    )

    ctx = SimulationStepContext(
        world=base_world,
        living_avatars=[parent, child],
        events=[event],
        month_stamp=base_world.month_stamp,
    )
    finalize_step(ctx)

    memories = base_world.event_manager.get_major_events_by_avatar(parent.id)
    assert len(memories) == 1
    assert "你得知 Child 发生了一件大事" in memories[0].content
    assert "broke through" in memories[0].content


@pytest.mark.asyncio
async def test_kill_propagation_adds_memory_and_hatred(base_world):
    killer = _make_avatar(base_world, "Killer")
    victim = _make_avatar(base_world, "Victim")
    parent = _make_avatar(base_world, "Parent")
    victim.acknowledge_parent(parent)

    for avatar in [killer, victim, parent]:
        base_world.avatar_manager.register_avatar(avatar)

    victim.hp.cur = 0
    events = await handle_battle_finish(
        base_world,
        killer,
        victim,
        (killer, victim, 100, 0),
        "Killer attacked Victim.",
        "describe battle",
        check_loot=False,
    )
    for event in events:
        base_world.event_manager.add_event(event)

    memories = base_world.event_manager.get_major_events_by_avatar(parent.id)
    assert any("Victim 被 Killer 杀害" in event.content for event in memories)
    assert parent.get_friendliness(killer) <= -80


@pytest.mark.asyncio
async def test_positive_bond_propagates_memory_and_warmth(base_world):
    lover_a = _make_avatar(base_world, "LoverA")
    lover_b = _make_avatar(base_world, "LoverB", gender=Gender.FEMALE)
    parent = _make_avatar(base_world, "Parent")
    lover_a.acknowledge_parent(parent)

    for avatar in [lover_a, lover_b, parent]:
        base_world.avatar_manager.register_avatar(avatar)

    action = Confess(lover_a, base_world)
    action._start_event_content = "LoverA confesses to LoverB."
    action._confess_success = True

    with patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=False):
        events = await action.finish(target_avatar=lover_b)

    for event in events:
        base_world.event_manager.add_event(event)

    memories = base_world.event_manager.get_major_events_by_avatar(parent.id)
    assert any("你得知 LoverA 与 LoverB结为道侣。" in event.content for event in memories)
    assert parent.get_friendliness(lover_b) >= 30


@pytest.mark.asyncio
async def test_master_disciple_bond_propagates_memory_and_warmth(base_world):
    disciple = _make_avatar(base_world, "Disciple")
    master = _make_avatar(base_world, "Master")
    parent = _make_avatar(base_world, "Parent")
    disciple.acknowledge_parent(parent)

    for avatar in [disciple, master, parent]:
        base_world.avatar_manager.register_avatar(avatar)

    record = {"kind": "find_master", "title_id": "fortune_title_master"}
    with patch("src.systems.fortune.random.random", side_effect=[0.0]), \
         patch("src.systems.fortune._choose_fortune_record", return_value=record), \
         patch("src.systems.fortune._find_potential_master", return_value=master), \
         patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=False):
        events = await try_trigger_fortune(disciple)

    for event in events:
        base_world.event_manager.add_event(event)

    memories = base_world.event_manager.get_major_events_by_avatar(parent.id)
    assert any("你得知 Disciple 与 Master建立师徒关系。" in event.content for event in memories)
    assert parent.get_friendliness(master) >= 15
