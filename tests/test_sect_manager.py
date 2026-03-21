import math
import pytest
from pathlib import Path
from unittest.mock import patch
from src.classes.core.world import World
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.core.avatar.core import Avatar
from src.classes.alignment import Alignment
from src.classes.age import Age
from src.systems.time import MonthStamp
from src.sim.managers.sect_manager import SectManager
from src.classes.event import Event
from src.classes.gender import Gender
from src.systems.battle import get_base_strength
from src.systems.cultivation import CultivationProgress

@pytest.fixture
def mock_world(base_world):
    """基于标准 base_world 构造一个带有两个宗门的世界。"""

    world: World = base_world
    game_map = world.map

    # 仅为 sect1 注册 SectRegion，使 sect1 有势力中心与收入；sect2 无总部则收入为 0
    from src.classes.environment.sect_region import SectRegion
    r1_id = 1001
    cors1 = [(0, 0)]
    r1 = SectRegion(id=r1_id, name="R1", desc="", sect_id=1, sect_name="测试宗门1", cors=cors1)
    game_map.regions[r1_id] = r1
    game_map.region_cors[r1_id] = cors1
    game_map.update_sect_regions()

    hq = SectHeadQuarter(name="测试驻地", desc="", image=Path(""))
    sect1 = Sect(
        id=1,
        name="测试宗门1",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )
    sect2 = Sect(
        id=2,
        name="测试宗门2",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )

    world.existed_sects = [sect1, sect2]
    # 确保 SectContext 中也记录本局启用宗门，便于 SectManager 统一读取
    world.sect_context.from_existed_sects(world.existed_sects)
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
    """宗门总战力与半径、半径计算 & 按格子结算灵石（无冲突时近似旧逻辑）。"""
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

    # 新逻辑下，收入按地图格子计算，这里只校验“> 0” 即可，具体数值在专门测试中断言
    assert sect1.magic_stone > 0

    # 验证 sect2 数据（空宗门）
    assert sect2.total_battle_strength == 0.0
    assert sect2.influence_radius == 1
    # 空宗门至少应保持 0 收入
    assert sect2.magic_stone == 0
    
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


def test_sect_income_conflict_sharing(base_world):
    """两个宗门半径为1且总部相邻，部分格子产生冲突时，应按格子平分灵石。"""
    world: World = base_world
    game_map = world.map

    # 选取相邻的两个坐标作为宗门总部区域
    r1_id, r2_id = 1001, 1002
    cors1 = [(1, 1)]
    cors2 = [(2, 1)]

    from src.classes.environment.sect_region import SectRegion

    r1 = SectRegion(id=r1_id, name="R1", desc="", sect_id=1, sect_name="S1", cors=cors1)
    r2 = SectRegion(id=r2_id, name="R2", desc="", sect_id=2, sect_name="S2", cors=cors2)

    game_map.regions[r1_id] = r1
    game_map.regions[r2_id] = r2
    game_map.region_cors[r1_id] = cors1
    game_map.region_cors[r2_id] = cors2
    game_map.update_sect_regions()

    hq = SectHeadQuarter(name="测试驻地", desc="", image=Path(""))
    sect1 = Sect(
        id=1,
        name="宗门A",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )
    sect2 = Sect(
        id=2,
        name="宗门B",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )

    world.existed_sects = [sect1, sect2]
    world.sect_context.from_existed_sects(world.existed_sects)

    # 固定战力，让半径都为 1
    with patch("src.sim.managers.sect_manager.get_base_strength", return_value=10.0):
        manager = SectManager(world)
        events = manager.update_sects()

    # 无成员时战力为 0，半径 = int(0)//10+1 == 1
    assert sect1.influence_radius == 1
    assert sect2.influence_radius == 1

    # 有事件产生
    assert len(events) == 2
    assert sect1.magic_stone > 0
    assert sect2.magic_stone > 0


def test_get_tile_owners_only_active(mock_world):
    """get_tile_owners 只返回激活宗门及其势力范围。"""
    sect1 = mock_world.existed_sects[0]
    sect2 = mock_world.existed_sects[1]
    # 标记 sect2 为非激活
    sect2.is_active = False

    manager = SectManager(mock_world)
    active_sects, tile_owners = manager.get_tile_owners()

    # 仅包含 sect1
    assert sect1 in active_sects
    assert sect2 not in active_sects

    # 所有格子只应包含 sect1 的 ID
    all_owner_ids = {sid for owners in tile_owners.values() for sid in owners}
    assert sect1.id in all_owner_ids or not all_owner_ids
    assert sect2.id not in all_owner_ids


def test_sect_manager_applies_member_upkeep(base_world):
    """年度结算应扣除成员按境界计算的固定供养支出。"""
    world: World = base_world
    game_map = world.map

    from src.classes.environment.sect_region import SectRegion

    region_id = 1001
    cors = [(1, 1)]
    region = SectRegion(id=region_id, name="R1", desc="", sect_id=1, sect_name="宗门A", cors=cors)
    game_map.regions[region_id] = region
    game_map.region_cors[region_id] = cors
    game_map.update_sect_regions()

    hq = SectHeadQuarter(name="测试驻地", desc="", image=Path(""))
    sect = Sect(
        id=1,
        name="宗门A",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )

    member = Avatar(
        world=world,
        name="弟子甲",
        id="member_a",
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE,
    )
    member.cultivation_progress = CultivationProgress(1)
    member.join_sect(sect, "DISCIPLE")
    member.is_dead = False

    world.existed_sects = [sect]
    world.sect_context.from_existed_sects(world.existed_sects)
    world.avatar_manager.avatars[member.id] = member

    manager = SectManager(world)
    snapshot = manager.get_snapshot()
    expected_income = int(manager.calculate_income_by_sect(snapshot).get(sect.id, 0.0))
    events = manager.update_sects()

    assert sect.influence_radius == 2
    assert sect.magic_stone == expected_income - 15
    assert len(events) == 1
    assert f"收入 {expected_income} 灵石" in events[0].content
    assert "支出 15 灵石" in events[0].content
    assert f"结余 {expected_income - 15} 灵石" in events[0].content
