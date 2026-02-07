import pytest
import random
from unittest.mock import MagicMock, patch
from src.classes.core.world import World
from src.classes.mortal import Mortal
from src.classes.core.avatar import Avatar, Gender
from src.systems.time import MonthStamp
from src.classes.relation.relation import Relation
from src.sim.avatar_awake import process_awakening, _process_bloodline_awakening, _process_wild_awakening
from src.utils.config import CONFIG

@pytest.fixture
def mock_world(base_world):
    return base_world

def test_process_bloodline_awakening(mock_world):
    """测试血脉觉醒逻辑"""
    # 1. 准备凡人
    mortal = Mortal(
        id="m1", 
        name="Test Mortal", 
        gender=Gender.MALE, 
        birth_month_stamp=MonthStamp(0), # 足够大
        parents=[]
    )
    mock_world.mortal_manager.register_mortal(mortal)
    
    # 2. 设置时间，使其满足年龄条件 (>=16岁)
    mock_world.month_stamp = MonthStamp(20 * 12) # 20岁
    
    # 3. 强制随机命中觉醒
    with patch("random.random", return_value=0.0): # < 0.05
        events = _process_bloodline_awakening(mock_world)
        
    # 4. 验证
    assert len(events) == 1
    # 兼容中英文环境 (虽然 conftest 强制中文，但双重检查更稳健)
    assert "awakened" in events[0].content or "觉醒" in events[0].content
    
    # 凡人应被移除
    assert mock_world.mortal_manager.get_mortal("m1") is None
    
    # Avatar 应被注册 (ID 复用)
    avatar = mock_world.avatar_manager.get_avatar("m1")
    assert avatar is not None
    assert avatar.name == "Test Mortal"
    assert avatar.cultivation_progress.level == 1 # 练气一层

def test_process_bloodline_awakening_age_limit(mock_world):
    """测试凡人超过觉醒年龄上限无法觉醒"""
    mortal = Mortal(
        id="m1", name="Old Mortal", gender=Gender.MALE, 
        birth_month_stamp=MonthStamp(0), parents=[]
    )
    mock_world.mortal_manager.register_mortal(mortal)
    
    # 设置为 80 岁 (> 60)
    mock_world.month_stamp = MonthStamp(80 * 12)
    
    with patch("random.random", return_value=0.0):
        events = _process_bloodline_awakening(mock_world)
        
    assert len(events) == 0
    assert mock_world.mortal_manager.get_mortal("m1") is not None # 还在，等老死
    assert mock_world.avatar_manager.get_avatar("m1") is None

def test_process_wild_awakening(mock_world):
    """测试野生觉醒逻辑"""
    # 强制随机命中
    # 注意：simulator.py 中 process_awakening 会调用它
    # 我们这里直接测试 _process_wild_awakening
    
    event = _process_wild_awakening(mock_world)
    
    assert event is not None
    assert "rogue cultivator" in event.content or "散修" in event.content
    
    # 验证产生了一个 Avatar
    # 由于 ID 是随机的，我们需要通过 pop_newly_born 来找
    new_ids = mock_world.avatar_manager.pop_newly_born()
    assert len(new_ids) == 1
    
    avatar = mock_world.avatar_manager.get_avatar(new_ids[0])
    assert avatar is not None
    assert avatar.sect is None # 散修

def test_awakening_integration(mock_world):
    """测试 process_awakening 集成调用"""
    # 同时触发血脉和野生
    mortal = Mortal(id="m1", name="M", gender=Gender.MALE, birth_month_stamp=MonthStamp(0), parents=[])
    mock_world.mortal_manager.register_mortal(mortal)
    mock_world.month_stamp = MonthStamp(20 * 12)
    
    # Patch random to always return 0 (hit both probabilities)
    with patch("random.random", return_value=0.0):
        events = process_awakening(mock_world)
        
    # 应该有 2 个事件 (1个血脉 + 1个野生)
    assert len(events) == 2
    
    # 验证结果
    assert mock_world.avatar_manager.get_avatar("m1") is not None
    assert len(mock_world.avatar_manager.pop_newly_born()) == 2 # m1 + wild
