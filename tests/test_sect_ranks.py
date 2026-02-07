"""
测试宗门等级系统
"""
import pytest
from src.systems.cultivation import CultivationProgress, Realm
from src.classes.sect_ranks import (
    SectRank,
    get_rank_from_realm,
    get_rank_display_name,
    should_auto_promote,
)
from src.classes.core.sect import sects_by_name
from src.classes.core.world import World
from src.classes.environment.map import Map
from src.systems.time import MonthStamp
from src.sim.avatar_init import make_avatars


def test_rank_from_realm():
    """测试境界到宗门职位的映射"""
    assert get_rank_from_realm(Realm.Qi_Refinement) == SectRank.OuterDisciple
    assert get_rank_from_realm(Realm.Foundation_Establishment) == SectRank.InnerDisciple
    assert get_rank_from_realm(Realm.Core_Formation) == SectRank.Elder
    assert get_rank_from_realm(Realm.Nascent_Soul) == SectRank.Patriarch


def test_rank_display_name():
    """测试职位显示名称"""
    assert get_rank_display_name(SectRank.Patriarch) == "掌门"
    assert get_rank_display_name(SectRank.Elder) == "长老"
    assert get_rank_display_name(SectRank.InnerDisciple) == "内门弟子"
    assert get_rank_display_name(SectRank.OuterDisciple) == "外门弟子"


def test_rank_comparison():
    """测试职位比较"""
    assert SectRank.Patriarch > SectRank.Elder
    assert SectRank.Elder > SectRank.InnerDisciple
    assert SectRank.InnerDisciple > SectRank.OuterDisciple
    assert SectRank.OuterDisciple < SectRank.Patriarch


def test_auto_promote():
    """测试自动晋升逻辑"""
    assert should_auto_promote(Realm.Qi_Refinement, Realm.Foundation_Establishment) == True
    assert should_auto_promote(Realm.Foundation_Establishment, Realm.Core_Formation) == True
    assert should_auto_promote(Realm.Core_Formation, Realm.Nascent_Soul) == True
    assert should_auto_promote(Realm.Qi_Refinement, Realm.Qi_Refinement) == False



def test_avatar_sect_rank_assignment(base_world):
    """测试avatar创建时宗门职位分配"""
    # 使用 base_world fixture，不需要 load_cultivation_world_map
    
    # 创建多个avatar
    avatars_dict = make_avatars(base_world, count=20, current_month_stamp=MonthStamp(100 * 12))
    avatars = list(avatars_dict.values())
    
    # 检查所有有宗门的avatar都有职位
    for avatar in avatars:
        if avatar.sect is not None:
            assert avatar.sect_rank is not None, f"{avatar.name} 有宗门但没有职位"
            # 职位应该匹配境界
            expected_rank = get_rank_from_realm(avatar.cultivation_progress.realm)
            # 如果不是预期职位，只可能是元婴修士被降为长老（因为掌门唯一性）
            if avatar.sect_rank != expected_rank:
                assert avatar.cultivation_progress.realm == Realm.Nascent_Soul
                assert avatar.sect_rank == SectRank.Elder
        else:
            assert avatar.sect_rank is None, f"{avatar.name} 散修不应该有职位"


def test_patriarch_uniqueness(base_world):
    """测试每个宗门只有一个掌门"""
    
    # 创建足够多的avatar
    avatars_dict = make_avatars(base_world, count=50, current_month_stamp=MonthStamp(100 * 12))
    avatars = list(avatars_dict.values())
    
    # 统计每个宗门的掌门数量
    sect_patriarchs = {}
    for avatar in avatars:
        if avatar.sect is not None and avatar.sect_rank == SectRank.Patriarch:
            sect_id = avatar.sect.id
            if sect_id not in sect_patriarchs:
                sect_patriarchs[sect_id] = []
            sect_patriarchs[sect_id].append(avatar.name)
    
    # 确保每个宗门最多只有一个掌门
    for sect_id, patriarchs in sect_patriarchs.items():
        assert len(patriarchs) <= 1, f"宗门 {sect_id} 有多个掌门: {patriarchs}"


def test_sect_str_display(base_world):
    """测试宗门信息显示"""
    
    avatars_dict = make_avatars(base_world, count=20, current_month_stamp=MonthStamp(100 * 12))
    avatars = list(avatars_dict.values())
    
    for avatar in avatars:
        sect_str = avatar.get_sect_str()
        if avatar.sect is None:
            assert sect_str == "散修"
        else:
            # 应该包含宗门名
            assert avatar.sect.name in sect_str
            # 应该包含职位名
            if avatar.sect_rank is not None:
                rank_name = get_rank_display_name(avatar.sect_rank, avatar.sect)
                assert rank_name in sect_str


def test_cultivation_breakthrough_promotion(base_world):
    """测试突破境界后自动晋升"""
    
    avatars_dict = make_avatars(base_world, count=10, current_month_stamp=MonthStamp(100 * 12))
    avatars = list(avatars_dict.values())
    
    # 找一个练气期的宗门弟子
    target_avatar = None
    for avatar in avatars:
        if avatar.sect is not None and avatar.cultivation_progress.realm == Realm.Qi_Refinement:
            target_avatar = avatar
            break
    
    if target_avatar is not None:
        # 记录原职位
        old_rank = target_avatar.sect_rank
        assert old_rank == SectRank.OuterDisciple
        
        # 突破到筑基
        target_avatar.cultivation_progress.level = 31  # 筑基初期
        target_avatar.update_cultivation(31)
        
        # 检查职位是否晋升
        assert target_avatar.sect_rank == SectRank.InnerDisciple
        assert target_avatar.sect_rank > old_rank



if __name__ == "__main__":
    pytest.main([__file__, "-v"])

