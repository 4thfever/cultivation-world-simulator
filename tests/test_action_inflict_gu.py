from unittest.mock import patch

from src.classes.action.inflict_gu import InflictGu
from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.persona import personas_by_name
from src.classes.relation.relations import get_friendliness
from src.classes.root import Root
from src.systems.cultivation import Realm
from src.systems.gu import (
    GU_LUANXIN,
    GU_QIANXIN,
    compute_gu_success_rate,
)
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _target(base_world, avatar_in_city, *, name="GuTarget") -> Avatar:
    target = Avatar(
        world=base_world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=avatar_in_city.pos_x,
        pos_y=avatar_in_city.pos_y,
        root=Root.WOOD,
        personas=[],
    )
    target.tile = avatar_in_city.tile
    base_world.avatar_manager.register_avatar(avatar_in_city)
    base_world.avatar_manager.register_avatar(target)
    return target


def _equip_gu_tool(avatar, item_id=2072):
    avatar.auxiliary = auxiliaries_by_id[item_id].instantiate()
    avatar.recalc_effects()


def test_inflict_gu_can_start_validates_target_and_gu_type(avatar_in_city, base_world):
    target = _target(base_world, avatar_in_city)
    action = InflictGu(avatar_in_city, base_world)

    ok, reason = action.can_start(target.name, GU_QIANXIN)
    assert ok is False
    assert "蛊具" in reason

    _equip_gu_tool(avatar_in_city)
    ok, reason = action.can_start(target.name, "unknown")
    assert ok is False
    assert "蛊类型" in reason

    ok, reason = action.can_start(avatar_in_city.name, GU_QIANXIN)
    assert ok is False
    assert "自己" in reason

    ok, reason = action.can_start(target.name, GU_QIANXIN)
    assert ok is True
    assert reason == ""


def test_inflict_gu_success_adds_temporary_gu_effect(avatar_in_city, base_world):
    target = _target(base_world, avatar_in_city)
    _equip_gu_tool(avatar_in_city, 2072)
    action = InflictGu(avatar_in_city, base_world)

    with patch("random.random", return_value=0.0):
        action._execute(target.name, GU_QIANXIN)

    assert len(target.temporary_effects) == 1
    effect = target.temporary_effects[0]
    assert effect["gu_type"] == GU_QIANXIN
    assert effect["caster_id"] == avatar_in_city.id
    assert effect["duration"] == 27
    assert effect["effects"] == {}


def test_inflict_gu_failure_detected_reduces_target_friendliness(avatar_in_city, base_world):
    target = _target(base_world, avatar_in_city)
    _equip_gu_tool(avatar_in_city, 2071)
    action = InflictGu(avatar_in_city, base_world)

    with patch("random.random", side_effect=[0.99, 0.0]):
        action._execute(target.name, GU_QIANXIN)

    assert target.temporary_effects == []
    assert get_friendliness(target, avatar_in_city) == -25


def test_gu_success_rate_uses_tool_persona_and_resistance_not_realm_or_luck(avatar_in_city, base_world):
    target = _target(base_world, avatar_in_city)
    _equip_gu_tool(avatar_in_city, 2073)
    avatar_in_city.personas = [personas_by_name["蛊师"]]
    target.temporary_effects.append({
        "source": "test_resistance",
        "effects": {"extra_gu_resistance_rate": 0.12},
        "start_month": int(base_world.month_stamp),
        "duration": 12,
    })
    avatar_in_city.recalc_effects()
    target.recalc_effects()

    base_rate = compute_gu_success_rate(avatar_in_city, target)
    assert base_rate == 0.64

    avatar_in_city.cultivation_progress.realm = Realm.Nascent_Soul
    target.cultivation_progress.realm = Realm.Nascent_Soul
    avatar_in_city.luck_base = 99
    target.luck_base = -99

    assert compute_gu_success_rate(avatar_in_city, target) == base_rate


def test_inflict_gu_finish_uses_objective_event_text(avatar_in_city, base_world):
    target = _target(base_world, avatar_in_city)
    _equip_gu_tool(avatar_in_city, 2074)
    action = InflictGu(avatar_in_city, base_world)

    with patch("random.random", return_value=0.0):
        action._execute(target.name, GU_LUANXIN)

    import asyncio

    events = asyncio.run(action.finish(target.name, GU_LUANXIN))
    assert events[0].content == f"{avatar_in_city.name}成功对{target.name}下了乱心蛊。"
