import pytest
from unittest.mock import patch

from src.classes.mutual_action.impart import Impart
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm, CultivationProgress
from src.systems.time import Year, Month, create_month_stamp
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.utils.id_generator import get_avatar_id


def _make_avatar(base_world, name: str, level: int, x: int = 0, y: int = 0) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=x,
        pos_y=y,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.cultivation_progress = CultivationProgress(level=level, exp=0)
    base_world.avatar_manager.avatars[avatar.name] = avatar
    return avatar


def _can_start(action: Impart, target: Avatar) -> tuple[bool, str]:
    with patch("src.classes.observe.is_within_observation", return_value=True):
        return action.can_start(target_avatar=target)


def test_parent_to_child_allowed(base_world):
    parent = _make_avatar(base_world, "parent", level=95)
    child = _make_avatar(base_world, "child", level=10)
    parent.acknowledge_child(child)

    action = Impart(parent, base_world)
    can_start, _ = _can_start(action, child)
    assert can_start is True


def test_child_to_parent_forbidden(base_world):
    parent = _make_avatar(base_world, "parent", level=95)
    child = _make_avatar(base_world, "child", level=10)
    parent.acknowledge_child(child)

    action = Impart(child, base_world)
    can_start, reason = _can_start(action, parent)
    assert can_start is False
    assert reason != ""


def test_grandparent_to_grandchild_allowed_depth2(base_world):
    grandparent = _make_avatar(base_world, "grandparent", level=95)
    parent = _make_avatar(base_world, "parent", level=20)
    grandchild = _make_avatar(base_world, "grandchild", level=10)
    grandparent.acknowledge_child(parent)
    parent.acknowledge_child(grandchild)

    action = Impart(grandparent, base_world)
    can_start, _ = _can_start(action, grandchild)
    assert can_start is True


def test_master_to_disciple_allowed(base_world):
    master = _make_avatar(base_world, "master", level=95)
    disciple = _make_avatar(base_world, "disciple", level=10)
    master.accept_disciple(disciple)

    action = Impart(master, base_world)
    can_start, _ = _can_start(action, disciple)
    assert can_start is True


def test_disciple_to_master_forbidden(base_world):
    master = _make_avatar(base_world, "master", level=95)
    disciple = _make_avatar(base_world, "disciple", level=10)
    master.accept_disciple(disciple)

    action = Impart(disciple, base_world)
    can_start, reason = _can_start(action, master)
    assert can_start is False
    assert reason != ""


def test_grandmaster_to_granddisciple_allowed_depth2(base_world):
    grandmaster = _make_avatar(base_world, "grandmaster", level=95)
    master = _make_avatar(base_world, "master", level=20)
    granddisciple = _make_avatar(base_world, "granddisciple", level=10)
    grandmaster.accept_disciple(master)
    master.accept_disciple(granddisciple)

    action = Impart(grandmaster, base_world)
    can_start, _ = _can_start(action, granddisciple)
    assert can_start is True


def test_depth3_forbidden_by_default(base_world):
    ancestor = _make_avatar(base_world, "ancestor", level=95)
    c1 = _make_avatar(base_world, "c1", level=20)
    c2 = _make_avatar(base_world, "c2", level=20)
    c3 = _make_avatar(base_world, "c3", level=10)

    ancestor.acknowledge_child(c1)
    c1.acknowledge_child(c2)
    c2.acknowledge_child(c3)

    action = Impart(ancestor, base_world)
    can_start, reason = _can_start(action, c3)
    assert can_start is False
    assert reason != ""
