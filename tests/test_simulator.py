import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.classes.action.move_to_direction import MoveToDirection
from src.classes.action_runtime import ActionInstance
from src.classes.core.avatar import Avatar, Gender
from src.classes.event import Event
from src.classes.root import Root
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.sim.simulator import Simulator
from src.sim.simulator_engine.phases import annual
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp


@pytest.mark.asyncio
async def test_simulator_step_moves_avatar_and_sets_tile(base_world, dummy_avatar, mock_llm_managers):
    dummy_avatar.pos_x = 1
    dummy_avatar.pos_y = 1
    dummy_avatar.tile = base_world.map.get_tile(1, 1)

    sim = Simulator(base_world)
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar

    action = MoveToDirection(dummy_avatar, base_world)
    direction = "East"
    action.start(direction=direction)
    dummy_avatar.current_action = ActionInstance(action=action, params={"direction": direction})

    await sim.step()

    assert dummy_avatar.pos_x == 3
    assert dummy_avatar.pos_y == 1
    assert dummy_avatar.tile is not None
    assert dummy_avatar.tile.x == 3
    assert dummy_avatar.tile.y == 1


@pytest.mark.asyncio
async def test_simulator_interaction_counting(base_world, dummy_avatar, mock_llm_managers):
    sim = Simulator(base_world)

    other_avatar = Avatar(
        world=base_world,
        name="OtherAvatar",
        id="other_id",
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=0,
        pos_y=0,
        root=Root.WOOD,
        alignment=Alignment.NEUTRAL,
    )

    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.avatar_manager.register_avatar(other_avatar)

    ev1 = Event(base_world.month_stamp, "phase1 interaction", related_avatars=[dummy_avatar.id, other_avatar.id])
    ev2 = Event(base_world.month_stamp, "phase2 interaction", related_avatars=[dummy_avatar.id, other_avatar.id])

    with patch(
        "src.sim.simulator_engine.phases.actions.phase_execute_actions",
        new=AsyncMock(return_value=[ev1]),
    ), patch(
        "src.sim.simulator_engine.phases.world.phase_passive_effects",
        new=AsyncMock(return_value=[ev2]),
    ):

        await sim.step()

    count = dummy_avatar.relation_interaction_states[other_avatar.id]["count"]
    assert count == 2


@pytest.mark.asyncio
async def test_simulator_event_deduplication(base_world, dummy_avatar, mock_llm_managers):
    sim = Simulator(base_world)
    base_world.avatar_manager.register_avatar(dummy_avatar)

    ev = Event(base_world.month_stamp, "duplicate event")
    ev_id = ev.id

    with patch(
        "src.sim.simulator_engine.phases.actions.phase_execute_actions",
        new=AsyncMock(return_value=[ev]),
    ), patch(
        "src.sim.simulator_engine.phases.world.phase_passive_effects",
        new=AsyncMock(return_value=[ev]),
    ):

        base_world.event_manager.add_event = MagicMock()
        await sim.step()

    target_calls = [
        call for call in base_world.event_manager.add_event.call_args_list if call.args[0].id == ev_id
    ]
    assert len(target_calls) == 1


@pytest.mark.asyncio
async def test_simulator_yearly_sect_thinking_runs_after_sect_update(base_world, mock_llm_managers):
    sim = Simulator(base_world)
    call_order = []

    def _update_sects():
        call_order.append("update_sects")
        return []

    async def _yearly_thinking(_simulator):
        call_order.append("yearly_thinking")
        return []

    with patch.object(sim.sect_manager, "update_sects", side_effect=_update_sects), patch(
        "src.sim.simulator_engine.phases.annual.phase_sect_yearly_thinking",
        new=AsyncMock(side_effect=_yearly_thinking),
    ):
        await sim.step()

    assert call_order == ["update_sects", "yearly_thinking"]


@pytest.mark.asyncio
async def test_simulator_yearly_sect_thinking_not_run_in_non_january(base_world, mock_llm_managers):
    base_world.month_stamp = create_month_stamp(Year(1), Month.FEBRUARY)
    sim = Simulator(base_world)

    with patch.object(sim.sect_manager, "update_sects") as mock_update_sects, patch(
        "src.sim.simulator_engine.phases.annual.phase_sect_yearly_thinking",
        new=AsyncMock(),
    ) as mock_yearly_thinking:
        await sim.step()

    mock_update_sects.assert_not_called()
    mock_yearly_thinking.assert_not_awaited()


@pytest.mark.asyncio
async def test_phase_sect_yearly_thinking_generates_event_with_related_sect(base_world, mock_llm_managers):
    base_world.start_year = 1
    base_world.month_stamp = create_month_stamp(Year(6), Month.JANUARY)

    sim = Simulator(base_world)
    sect = MagicMock()
    sect.id = 77
    sect.name = "Test Sect"
    sect.yearly_thinking = ""

    base_world.existed_sects = [sect]
    base_world.event_manager._storage = MagicMock()
    base_world.event_manager._storage.get_events.return_value = ([], None)

    with patch("src.classes.core.sect.get_sect_decision_context", return_value=MagicMock()), patch(
        "src.sim.simulator_engine.phases.annual.SectDecider.decide",
        new=AsyncMock(return_value="secure borders first"),
    ), patch(
        "src.sim.simulator_engine.phases.annual.t",
        side_effect=lambda key, **kwargs: "{sect_name} sect thinking: {thinking}".format(**kwargs)
        if key == "game.sect_thinking_event"
        else key,
    ):
        events = await annual.phase_sect_yearly_thinking(sim)

    assert len(events) == 1
    event = events[0]
    assert event.related_sects == [77]
    assert "Test Sect sect thinking:" in event.content
    assert "secure borders first" in event.content


@pytest.mark.asyncio
async def test_phase_sect_yearly_thinking_skips_non_interval_year(base_world, mock_llm_managers):
    base_world.start_year = 1
    base_world.month_stamp = create_month_stamp(Year(4), Month.JANUARY)

    sim = Simulator(base_world)
    sect = MagicMock()
    sect.id = 77
    sect.name = "Test Sect"
    sect.yearly_thinking = ""

    base_world.existed_sects = [sect]
    base_world.event_manager._storage = MagicMock()
    base_world.event_manager._storage.get_events.return_value = ([], None)

    with patch("src.classes.core.sect.get_sect_decision_context", return_value=MagicMock()), patch(
        "src.sim.simulator_engine.phases.annual.SectDecider.decide",
        new=AsyncMock(return_value="should not happen"),
    ) as mock_decide:
        events = await annual.phase_sect_yearly_thinking(sim)

    assert events == []
    mock_decide.assert_not_awaited()
