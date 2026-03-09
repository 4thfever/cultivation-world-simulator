import math
import pytest
from src.classes.core.world import World
from src.classes.core.sect import Sect
from src.classes.core.avatar.core import Avatar
from src.classes.age import Age
from src.systems.time import MonthStamp
from src.sim.managers.sect_manager import SectManager
from src.classes.event import Event
from src.classes.gender import Gender

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

def create_mock_avatar(world, name, sect, battle_strength):
    # 手动创建一个简化的Avatar对象
    avatar = Avatar(
        world=world,
        name=name,
        id=f"avatar_{name}",
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE
    )
    # mock战力
    avatar.base_battle_strength = battle_strength
    if sect:
        avatar.join_sect(sect, "DISCIPLE") # 随便给个职位
    return avatar

def test_sect_manager_update(mock_world):
    sect1 = mock_world.existed_sects[0]
    sect2 = mock_world.existed_sects[1]
    
    manager = SectManager(mock_world)
    
    # 给sect1添加几个成员，sect2没有成员
    a1 = create_mock_avatar(mock_world, "张三", sect1, 100)
    a2 = create_mock_avatar(mock_world, "李四", sect1, 120)
    
    # 模拟在世
    a1.is_dead = False
    a2.is_dead = False
    
    mock_world.avatar_manager.avatars[a1.id] = a1
    mock_world.avatar_manager.avatars[a2.id] = a2
    
    # 模拟更新
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
    
    # 灵石 = area * 100 = 36500
    assert sect1.magic_stone == 36500
    
    # 验证sect2数据（空宗门）
    assert sect2.total_battle_strength == 0.0
    assert sect2.influence_radius == 1
    # 空宗门也会有一格地盘： 2*1 + 2*1 + 1 = 5, income = 500
    assert sect2.magic_stone == 500
    
    # 验证事件生成
    assert len(events) == 2
    assert all(isinstance(e, Event) for e in events)
    assert events[0].related_sects == [1]
    assert events[1].related_sects == [2]
