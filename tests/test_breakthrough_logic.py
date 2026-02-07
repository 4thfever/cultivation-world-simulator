import pytest
from src.systems.cultivation import CultivationProgress, Realm, Stage, REALM_ORDER, LEVELS_PER_REALM

def test_breakthrough_normal(dummy_avatar):
    """
    测试正常突破逻辑：从练气圆满突破到筑基前期
    """
    # 练气圆满是 30 级 (LEVELS_PER_REALM * 1)
    qi_max_level = 30
    
    # 设置角色状态
    cp = CultivationProgress(level=qi_max_level, exp=0)
    dummy_avatar.cultivation_progress = cp
    
    # 验证当前状态
    assert cp.realm == Realm.Qi_Refinement
    assert cp.is_in_bottleneck() is True
    assert cp.can_break_through() is True
    
    # 执行突破
    cp.break_through()
    
    # 验证突破后状态
    # 应该升级到 31 级
    assert cp.level == 31
    # 境界应该是 筑基
    assert cp.realm == Realm.Foundation_Establishment
    # 阶段应该是 前期
    assert cp.stage == Stage.Early_Stage
    # 不再处于瓶颈
    assert cp.is_in_bottleneck() is False

def test_breakthrough_max_realm_limit(dummy_avatar):
    """
    测试最高境界限制：元婴圆满（目前最高等级）不能再突破
    """
    # 计算最高等级
    # 目前有 4 个境界，每个 30 级，最高 120 级
    max_level = len(REALM_ORDER) * LEVELS_PER_REALM
    
    # 设置角色状态为最高等级
    cp = CultivationProgress(level=max_level, exp=0)
    dummy_avatar.cultivation_progress = cp
    
    # 验证当前状态
    assert cp.realm == Realm.Nascent_Soul
    # 理论上它是 30/60/90/120，模 30 为 0，所以 is_in_bottleneck 会返回 True
    assert cp.is_in_bottleneck() is True
    
    # 关键测试点：can_break_through 应该返回 False，因为已经封顶了
    assert cp.can_break_through() is False

def test_not_in_bottleneck(dummy_avatar):
    """
    测试非瓶颈期不能突破
    """
    # 随便设一个中间等级，比如 15 级（练气中期）
    cp = CultivationProgress(level=15, exp=0)
    dummy_avatar.cultivation_progress = cp
    
    assert cp.is_in_bottleneck() is False
    assert cp.can_break_through() is False

def test_breakthrough_intermediate_bottleneck(dummy_avatar):
    """
    测试中间境界的突破：筑基圆满 -> 金丹
    """
    # 筑基圆满是 60 级
    foundation_max_level = 60
    
    cp = CultivationProgress(level=foundation_max_level, exp=0)
    dummy_avatar.cultivation_progress = cp
    
    assert cp.realm == Realm.Foundation_Establishment
    assert cp.can_break_through() is True
    
    cp.break_through()
    
    assert cp.level == 61
    assert cp.realm == Realm.Core_Formation
    assert cp.stage == Stage.Early_Stage
