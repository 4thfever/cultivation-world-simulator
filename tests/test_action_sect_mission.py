import pytest
from unittest.mock import AsyncMock, patch

from src.classes.action.sect_mission import SectMission, SECT_TASK_DEFINITIONS
from src.classes.action_runtime import ActionStatus
from src.classes.core.sect import sects_by_id
from src.classes.effect.consts import EXTRA_SECT_MISSION_SUCCESS_RATE
from src.classes.environment.sect_region import SectRegion
from src.classes.environment.tile import Tile, TileType
from src.classes.event import Event
from src.systems.cultivation import Realm


def _place_avatar_in_own_sect_hq(avatar, sect):
    region = SectRegion(
        id=9000 + int(sect.id),
        name=sect.headquarter.name,
        desc=sect.headquarter.desc,
        sect_name=sect.name,
        sect_id=sect.id,
    )
    avatar.tile = Tile(TileType.SECT, 0, 0, region=region)
    avatar.sect = sect
    sect.add_member(avatar)
    avatar.recalc_effects()
    return region


@pytest.fixture
def sect_mission_avatar(dummy_avatar, base_world):
    sect = next(iter(sects_by_id.values()))
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    base_world.avatar_manager.register_avatar(dummy_avatar)
    _place_avatar_in_own_sect_hq(dummy_avatar, sect)
    return dummy_avatar


def test_sect_mission_can_start_requires_membership_and_hq(dummy_avatar, base_world):
    action = SectMission(dummy_avatar, base_world)
    can_start, reason = action.can_start()
    assert can_start is False
    assert ("宗门" in reason) or ("总部" in reason)


def test_sect_mission_can_possibly_start(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    assert action.can_possibly_start() is True

    sect_mission_avatar.sect = None
    assert action.can_possibly_start() is False


def test_sect_mission_start_uses_realm_filtered_pool(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    assert all(Realm.Qi_Refinement in task.allowed_realms for task in action._get_candidate_tasks())
    assert all(Realm.Core_Formation not in task.allowed_realms for task in action._get_candidate_tasks())

    with patch("src.classes.action.sect_mission.random.choices", return_value=[action._get_candidate_tasks()[0]]), \
         patch("src.classes.action.sect_mission.random.choice", side_effect=[3, "headquarter"]):
        start_event = action.start()

    assert start_event.related_sects == [int(sect_mission_avatar.sect.id)]
    assert action.duration_months == 3
    assert action.task_title
    assert action.base_success_rate > 0
    assert action.reward_magic_stones > 0
    assert action.reward_contribution > 0
    assert action.task_id in {task.id for task in SECT_TASK_DEFINITIONS}


def test_sect_mission_calc_success_rate_uses_effect_and_luck(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    action.base_success_rate = 0.5
    sect_mission_avatar.luck_base = 10
    sect_mission_avatar.temporary_effects.append(
        {
            "source": "test_bonus",
            "effects": {EXTRA_SECT_MISSION_SUCCESS_RATE: 0.1},
            "start_month": int(sect_mission_avatar.world.month_stamp),
            "duration": 12,
        }
    )
    sect_mission_avatar.recalc_effects()

    assert action.calc_success_rate() == pytest.approx(0.62)


@pytest.mark.asyncio
async def test_sect_mission_finish_success_rewards_and_story(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    action.task_title = "巡逻山门"
    action.task_id = "sect_task_patrol_gate"
    action.task_category = "patrol"
    action.issuer_type = "headquarter"
    action.duration_months = 4
    action.base_success_rate = 0.8
    action.reward_magic_stones = 56
    action.reward_contribution = 16
    action.fail_damage_ratio = 0.2
    action._start_event_content = "开始事件"

    with patch("src.classes.action.sect_mission.random.random", return_value=0.1), \
         patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=True), \
         patch("src.classes.story_event_service.StoryTeller.tell_story", new_callable=AsyncMock, return_value="任务故事"):
        events = await action.finish()

    assert sect_mission_avatar.magic_stone.value == 56
    assert sect_mission_avatar.sect_contribution == 16
    assert len(events) == 2
    assert events[0].related_sects == [int(sect_mission_avatar.sect.id)]
    assert events[1].is_story is True


@pytest.mark.asyncio
async def test_sect_mission_finish_failure_can_kill(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    action.task_title = "调查夜间异动"
    action.task_id = "sect_task_investigate_night_anomaly"
    action.task_category = "investigate"
    action.issuer_type = "headquarter"
    action.duration_months = 5
    action.base_success_rate = 0.2
    action.reward_magic_stones = 0
    action.reward_contribution = 0
    action.fail_damage_ratio = 0.5
    action._start_event_content = "开始事件"
    sect_mission_avatar.hp.cur = 10

    with patch("src.classes.action.sect_mission.random.random", return_value=0.95), \
         patch("src.classes.action.sect_mission.random.uniform", return_value=1.0), \
         patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=False):
        events = await action.finish()

    assert len(events) == 1
    assert sect_mission_avatar.is_dead is True
    assert sect_mission_avatar.id in sect_mission_avatar.world.avatar_manager.dead_avatars
    assert "殒命" in events[0].content


@pytest.mark.asyncio
async def test_sect_mission_step_and_save_load(sect_mission_avatar):
    action = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    with patch("src.classes.action.sect_mission.random.choices", return_value=[action._get_candidate_tasks()[0]]), \
         patch("src.classes.action.sect_mission.random.choice", side_effect=[6, "headquarter"]):
        action.start()

    result = action.step()
    assert result.status == ActionStatus.RUNNING

    save_data = action.get_save_data()
    loaded = SectMission(sect_mission_avatar, sect_mission_avatar.world)
    loaded.load_save_data(save_data)

    assert loaded.task_id == action.task_id
    assert loaded.task_title == action.task_title
    assert loaded.duration_months == action.duration_months
