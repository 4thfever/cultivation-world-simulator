import pytest
import random
from unittest.mock import MagicMock, patch
from src.classes.action.meditate import Meditate
from src.classes.action.educate import Educate
from src.classes.environment.region import CityRegion, CultivateRegion, Region
from src.classes.environment.tile import TileType, Tile
from src.classes.core.avatar import Avatar
from src.systems.cultivation import Realm, CultivationProgress

# --- 禅定 (Meditate) 测试 ---

def test_meditate_can_start(dummy_avatar):
    # 1. 默认状态（散修）无法禅定（因为 legal_actions 默认为空，不包含 Meditate）
    # 注意：根据 meditate.py 的逻辑，必须显式拥有 "Meditate" 权限
    can, reason = Meditate(dummy_avatar, dummy_avatar.world).can_start()
    assert can is False
    assert "不支持禅定" in reason

    # 2. 添加佛门权限
    # dummy_avatar.effects 是只读属性，需要 mock 一个临时效果
    dummy_avatar.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Meditate"]
        },
        "start_month": int(dummy_avatar.world.month_stamp),
        "duration": 10
    })
    
    can, reason = Meditate(dummy_avatar, dummy_avatar.world).can_start()
    assert can is True

    # 3. 瓶颈状态
    dummy_avatar.cultivation_progress.level = 30 # 练气圆满瓶颈
    can, reason = Meditate(dummy_avatar, dummy_avatar.world).can_start()
    assert can is False
    assert "瓶颈" in reason

def test_meditate_execution_normal(dummy_avatar):
    """测试普通禅定（未顿悟）"""
    dummy_avatar.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Meditate"]
        },
        "start_month": int(dummy_avatar.world.month_stamp),
        "duration": 10
    })
    
    action = Meditate(dummy_avatar, dummy_avatar.world)
    
    # Mock 随机数使其不触发顿悟 (prob < 0.1, random > 0.1)
    # BASE_PROB = 0.1
    random.seed(42) 
    # random.random() -> 0.639... > 0.1 -> 普通禅定
    
    initial_exp = dummy_avatar.cultivation_progress.exp
    action._execute()
    
    # 练气期 multiplier = 1
    # 普通经验 BASE_EXP = 10
    expected_gain = 10 * 1 
    assert dummy_avatar.cultivation_progress.exp == initial_exp + expected_gain
    assert action._last_is_epiphany is False

def test_meditate_execution_epiphany(dummy_avatar):
    """测试禅定顿悟"""
    # dummy_avatar.effects 是只读属性，需要 mock 一个临时效果
    dummy_avatar.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Meditate"],
            "extra_meditate_prob": 1.0 # 强制顿悟：增加极大概率
        },
        "start_month": int(dummy_avatar.world.month_stamp),
        "duration": 10
    })
    
    action = Meditate(dummy_avatar, dummy_avatar.world)
    
    # Mock add_exp，避免升级消耗导致数值不匹配
    dummy_avatar.cultivation_progress.add_exp = MagicMock()
    
    action._execute()
    
    # 练气期 multiplier = 1 (REALM_RANK.get(Qi_Refinement, 0) + 1 = 1)
    # 顿悟经验 EPIPHANY_EXP = 1500
    # 额外加成 multiplier = 0
    # exp = 1500 * 1 * (1 + 0) = 1500
    expected_gain = 1500 * 1
    
    dummy_avatar.cultivation_progress.add_exp.assert_called_with(expected_gain)
    assert action._last_is_epiphany is True

def test_meditate_realm_bonus(dummy_avatar):
    """测试境界加成"""
    # 提升至筑基期
    # 注意：直接修改 realm 并不够，因为 REALM_RANK 可能依赖其他
    # 还要确保 REALM_RANK.get(realm) 正确
    dummy_avatar.cultivation_progress.realm = Realm.Foundation_Establishment
    # 筑基期 rank index = 1 -> multiplier = 2
    
    dummy_avatar.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Meditate"],
            "extra_meditate_prob": -1.0 # 抵消概率，强制普通禅定
        },
        "start_month": int(dummy_avatar.world.month_stamp),
        "duration": 10
    })
    
    action = Meditate(dummy_avatar, dummy_avatar.world)
    
    # Mock add_exp
    dummy_avatar.cultivation_progress.add_exp = MagicMock()
    
    action._execute()
    
    # 10 * 2 = 20
    dummy_avatar.cultivation_progress.add_exp.assert_called_with(20)

# --- 教化 (Educate) 测试 ---

def test_educate_can_start(avatar_in_city):
    # avatar_in_city 已经在 CityRegion
    
    # 1. 无权限
    can, reason = Educate(avatar_in_city, avatar_in_city.world).can_start()
    assert can is False
    assert "不支持教化" in reason
    
    # 2. 添加儒门权限 (通过 temporary_effects)
    avatar_in_city.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Educate"]
        },
        "start_month": int(avatar_in_city.world.month_stamp),
        "duration": 10
    })
    # 强制重算属性
    avatar_in_city.recalc_effects()
    
    can, reason = Educate(avatar_in_city, avatar_in_city.world).can_start()
    assert can is True
    
    # 3. 移动到野外 (NormalRegion)
    avatar_in_city.tile.region = CultivateRegion(id=99, name="Cave", desc="Cave")
    can, reason = Educate(avatar_in_city, avatar_in_city.world).can_start()
    assert can is False
    assert "必须在城市" in reason

def test_educate_execution(avatar_in_city):
    """测试教化经验计算"""
    # 同上，使用 temporary_effects
    avatar_in_city.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Educate"]
        },
        "start_month": int(avatar_in_city.world.month_stamp),
        "duration": 10
    })
    # 强制重算属性
    avatar_in_city.recalc_effects()
    
    region = avatar_in_city.tile.region
    region.prosperity = 50.0 # 标准繁荣度
    
    action = Educate(avatar_in_city, avatar_in_city.world)
    
    # Mock add_exp
    avatar_in_city.cultivation_progress.add_exp = MagicMock()
    
    # 固定随机数防止繁荣度变化干扰（虽然这里主要测经验）
    random.seed(1)
    
    action._execute()
    
    # 练气期 multiplier = 1
    # 繁荣度系数 = 50 / 50 = 1.0
    # 基准经验 BASE_EXP_TOTAL = 150
    # 150 * 1 * 1 = 150
    # avatar_in_city.cultivation_progress.add_exp.assert_called_with(150)
    
    dummy_avatar = avatar_in_city
    dummy_avatar.cultivation_progress.add_exp.assert_called()
    args, _ = dummy_avatar.cultivation_progress.add_exp.call_args
    # 允许一定的误差，或者先断言调用了
    assert args[0] == 150

def test_educate_prosperity_effect(avatar_in_city):
    """测试教化对繁荣度的影响"""
    avatar_in_city.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Educate"]
        },
        "start_month": int(avatar_in_city.world.month_stamp),
        "duration": 10
    })
    # 强制重算属性
    avatar_in_city.recalc_effects()
    
    region = avatar_in_city.tile.region
    region.prosperity = 50.0
    
    action = Educate(avatar_in_city, avatar_in_city.world)
    
    # 强制触发
    # 使用 patch.object 覆盖 action._execute 内部的 random.random
    # 注意：由于是在 action 模块内部 import random，通常需要 patch 'src.classes.action.educate.random.random'
    # 或者直接 patch 'random.random' 如果是直接 import random
    with patch('src.classes.action.educate.random.random', return_value=0.1):
        action._execute()
        
    assert region.prosperity == 50.2

def test_educate_high_prosperity_bonus(avatar_in_city):
    """测试高繁荣度加成"""
    avatar_in_city.temporary_effects.append({
        "source": "test_buff",
        "effects": {
            "legal_actions": ["Educate"]
        },
        "start_month": int(avatar_in_city.world.month_stamp),
        "duration": 10
    })
    # 强制重算属性
    avatar_in_city.recalc_effects()
    
    region = avatar_in_city.tile.region
    region.prosperity = 100.0 # 双倍繁荣度
    
    action = Educate(avatar_in_city, avatar_in_city.world)
    
    # Mock add_exp
    avatar_in_city.cultivation_progress.add_exp = MagicMock()
    
    action._execute()
    
    # 150 * 1 * (100/50) = 300
    expected = 150 * 1 * 2.0
    # avatar_in_city.cultivation_progress.add_exp.assert_called_with(int(expected))
    
    dummy_avatar = avatar_in_city
    dummy_avatar.cultivation_progress.add_exp.assert_called()
    args, _ = dummy_avatar.cultivation_progress.add_exp.call_args
    assert args[0] == int(expected)
