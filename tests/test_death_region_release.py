
import pytest
from src.classes.death_reason import DeathReason, DeathType
from src.classes.death import handle_death
from src.classes.environment.region import CultivateRegion, EssenceType

def test_death_releases_region(base_world, dummy_avatar):
    """测试死亡时释放占领的洞府"""
    # 1. 创建一个修炼区域
    region = CultivateRegion(
        id=1001,
        name="Test Cave",
        desc="A test cave",
        essence_type=EssenceType.GOLD,
        essence_density=10
    )
    # 将区域添加到地图
    base_world.map.regions[region.id] = region
    
    # 2. 让角色占领该区域
    dummy_avatar.occupy_region(region)
    
    # 验证占领成功
    assert region.host_avatar == dummy_avatar
    assert region in dummy_avatar.owned_regions
    
    # 3. 角色死亡
    reason = DeathReason(DeathType.OLD_AGE)
    handle_death(base_world, dummy_avatar, reason)
    
    # 4. 验证洞府已被释放
    assert region.host_avatar is None
    assert len(dummy_avatar.owned_regions) == 0
    assert dummy_avatar.is_dead is True

def test_occupy_region_logic(base_world, dummy_avatar):
    """测试占领逻辑的双向绑定和抢夺"""
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.time import create_month_stamp, Year, Month

    # 创建第二个角色
    other_avatar = Avatar(
        world=base_world,
        name="Other",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0, pos_y=0,
        root=Root.WOOD,
        alignment=Alignment.RIGHTEOUS
    )
    
    region = CultivateRegion(
        id=1002,
        name="Test Cave 2",
        desc="Another test cave",
        essence_type=EssenceType.WOOD,
        essence_density=10
    )
    
    # 1. dummy_avatar 占领
    dummy_avatar.occupy_region(region)
    assert region.host_avatar == dummy_avatar
    assert region in dummy_avatar.owned_regions
    
    # 2. other_avatar 抢夺
    other_avatar.occupy_region(region)
    
    # 验证所有权转移
    assert region.host_avatar == other_avatar
    assert region in other_avatar.owned_regions
    
    # 验证旧主已释放
    assert region not in dummy_avatar.owned_regions

def test_remove_avatar_releases_region(base_world, dummy_avatar):
    """测试彻底删除角色时释放占领的洞府"""
    # 1. 创建一个修炼区域
    region = CultivateRegion(
        id=1003,
        name="Test Cave 3",
        desc="Yet another test cave",
        essence_type=EssenceType.WATER,
        essence_density=10
    )
    base_world.map.regions[region.id] = region
    
    # 2. 注册并占领
    base_world.avatar_manager.register_avatar(dummy_avatar)
    dummy_avatar.occupy_region(region)
    
    assert region.host_avatar == dummy_avatar
    
    # 3. 彻底删除角色
    base_world.avatar_manager.remove_avatar(dummy_avatar.id)
    
    # 4. 验证洞府已被释放
    assert region.host_avatar is None
    # 注意：此时 dummy_avatar 对象可能还在内存中，但已经从管理器移除
    # 它的 owned_regions 应该被清空了
    assert len(dummy_avatar.owned_regions) == 0
