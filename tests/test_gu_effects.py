from unittest.mock import patch

from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.relation.relations import get_friendliness
from src.classes.root import Root
from src.systems.cultivation import Realm
from src.systems.gu import (
    GU_LUANXIN,
    GU_QIANXIN,
    GU_SHIXUE,
    GU_SHIYUAN,
    build_gu_effect,
    process_avatar_gu_effects,
)
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _avatar(base_world, name):
    avatar = Avatar(
        world=base_world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        root=Root.WOOD,
        personas=[],
    )
    base_world.avatar_manager.register_avatar(avatar)
    return avatar


def _gu_effect(caster, gu_type, *, start_month=0, last_tick_month=-1):
    effect = build_gu_effect(caster, gu_type)
    effect["start_month"] = start_month
    effect["last_tick_month"] = last_tick_month
    return effect


def test_qianxin_gu_adds_friendliness_once_per_month(base_world):
    caster = _avatar(base_world, "Caster")
    target = _avatar(base_world, "Target")
    target.temporary_effects.append(_gu_effect(caster, GU_QIANXIN))

    process_avatar_gu_effects(target, 0)
    process_avatar_gu_effects(target, 0)
    assert get_friendliness(target, caster) == 1

    process_avatar_gu_effects(target, 1)
    assert get_friendliness(target, caster) == 2


def test_shixue_gu_reduces_hp_monthly(base_world):
    caster = _avatar(base_world, "Caster")
    target = _avatar(base_world, "Target")
    target.hp.max = 200
    target.hp.cur = 200
    target.temporary_effects.append(_gu_effect(caster, GU_SHIXUE))

    process_avatar_gu_effects(target, 0)

    assert target.hp.cur == 196


def test_shiyuan_gu_reduces_exp_without_negative(base_world):
    caster = _avatar(base_world, "Caster")
    target = _avatar(base_world, "Target")
    target.cultivation_progress.exp = 30
    target.temporary_effects.append(_gu_effect(caster, GU_SHIYUAN))

    process_avatar_gu_effects(target, 0)

    assert target.cultivation_progress.exp == 0


def test_luanxin_gu_reduces_exp_when_triggered(base_world):
    caster = _avatar(base_world, "Caster")
    target = _avatar(base_world, "Target")
    target.cultivation_progress.exp = 100
    target.temporary_effects.append(_gu_effect(caster, GU_LUANXIN))

    with patch("random.random", return_value=0.0):
        events = process_avatar_gu_effects(target, 0)

    assert target.cultivation_progress.exp == 20
    assert len(events) == 1
    assert "乱心蛊" in events[0].content


def test_expired_gu_effect_does_not_tick(base_world):
    caster = _avatar(base_world, "Caster")
    target = _avatar(base_world, "Target")
    target.cultivation_progress.exp = 100
    effect = _gu_effect(caster, GU_SHIYUAN, start_month=0)
    effect["duration"] = 1
    target.temporary_effects.append(effect)

    process_avatar_gu_effects(target, 1)

    assert target.cultivation_progress.exp == 100
