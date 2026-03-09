import math
import pytest
from unittest.mock import patch
from src.classes.core.world import World
from src.classes.core.sect import Sect
from src.classes.core.avatar.core import Avatar
from src.classes.age import Age
from src.systems.time import MonthStamp
from src.sim.managers.sect_manager import SectManager
from src.classes.event import Event
from src.classes.gender import Gender
from src.systems.battle import get_base_strength

@pytest.fixture
def mock_world():
    # 简单的Map mock
    class MockMap:
        def get_tile(self, x, y):
            return None
            
    world = World(map=MockMap(), month_stamp=MonthStamp(1))
    
    # 构造假宗门
    sect1 = Sect(id=1, name="测试宗门1", desc="", orthodoxy_id="jianxiu", member_act_style="", alignment="NEUTRAL", preferred_weapon="SWORD", headquarter="", technique_names=[])
    sect2 = Sect(id=2, name="测试宗门2", desc="", orthodoxy_id="fuxiu", member_act_style="", alignment="GOOD", preferred_weapon="STAFF", headquarter="", technique_names=[])
    
    world.existed_sects = [sect1, sect2]
    return world

def create_mock_avatar(world, name, sect, battle_strength=None):
    # 手动创建一个简化的Avatar对象；battle_strength 仅在被 patch 时用于断言，实际战力由 get_base_strength 计算
    avatar = Avatar(
        world=world,
        name=name,
        id=f"avatar_{name}",
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE
    )
    if battle_strength is not None:
        avatar.base_battle_strength = battle_strength  # 仅用于 test_sect_manager_update 中 patch 的返回值
    if sect:
        avatar.join_sect(sect, "DISCIPLE")
    return avatar

def test_sect_manager_update(mock_world):
    """宗门总战力与半径、灵石计算：战力来自 get_base_strength(成员)。"""
    sect1 = mock_world.existed_sects[0]
    sect2 = mock_world.existed_sects[1]
    manager = SectManager(mock_world)

    a1 = create_mock_avatar(mock_world, "张三", sect1, 100)
    a2 = create_mock_avatar(mock_world, "李四", sect1, 120)
    a1.is_dead = False
    a2.is_dead = False
    mock_world.avatar_manager.avatars[a1.id] = a1
    mock_world.avatar_manager.avatars[a2.id] = a2

    # SectManager 使用 get_base_strength(avatar)，此处 patch 为固定值以断言公式
    with patch("src.sim.managers.sect_manager.get_base_strength", side_effect=[100.0, 120.0]):
        events = manager.update_sects()
    
    # 验证sect1数据
    # 计算公式：max_str + log(sum(exp(s - max_str)))
    # max_str = 120
    # s1 = 100 -> exp(-20) ≈ 0
    # s2 = 120 -> exp(0) = 1
    # total ≈ 120 + log(1) = 120
    assert sect1.total_battle_strength >= 120
    assert sect1.total_battle_strength < 121
    
    # 半径计算: int(120) // 10 + 1 = 13
    assert sect1.influence_radius == 13
    
    # 面积 = 2 * R^2 + 2 * R + 1
    # 2 * 169 + 26 + 1 = 338 + 27 = 365
    expected_area = 2 * (13**2) + 2 * 13 + 1
    assert expected_area == 365
    
    # 灵石 = area * 10 = 3650
    assert sect1.magic_stone == 3650
    
    # 验证sect2数据（空宗门）
    assert sect2.total_battle_strength == 0.0
    assert sect2.influence_radius == 1
    # 空宗门也会有一格地盘： 2*1 + 2*1 + 1 = 5, income = 50
    assert sect2.magic_stone == 50
    
    # 验证事件生成
    assert len(events) == 2
    assert all(isinstance(e, Event) for e in events)
    assert events[0].related_sects == [1]
    assert events[1].related_sects == [2]


def test_sect_total_strength_uses_avatar_battle_strength(mock_world):
    """宗门总战力必须使用 get_base_strength(成员)，即境界+效果算出的战斗力。"""
    from src.systems.cultivation import CultivationProgress

    sect = mock_world.existed_sects[0]
    manager = SectManager(mock_world)

    # 筑基前期：Foundation_Establishment=20, Early_Stage=0 -> 20
    avatar = Avatar(
        world=mock_world,
        name="王五",
        id="avatar_wang",
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE
    )
    avatar.cultivation_progress = CultivationProgress(31)  # 筑基前期
    avatar.join_sect(sect, "DISCIPLE")
    avatar.is_dead = False
    mock_world.avatar_manager.avatars[avatar.id] = avatar

    expected_strength = get_base_strength(avatar)  # 20.0
    events = manager.update_sects()

    assert sect.total_battle_strength >= 19.0
    assert sect.total_battle_strength <= 21.0
    # 半径 = int(20) // 10 + 1 = 3
    assert sect.influence_radius == 3
    assert len(events) >= 1
