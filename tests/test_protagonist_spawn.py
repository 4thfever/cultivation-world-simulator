import pytest
from unittest.mock import patch, MagicMock
from src.utils.protagonist import spawn_protagonists
from src.classes.relation.relation import Relation
from src.classes.gender import Gender
from src.systems.time import MonthStamp, create_month_stamp, Year, Month

# Mock 配置数据
# 我们使用一组受控的数据来测试生成逻辑和关系绑定
MOCK_PROTAGONIST_CONFIG = [
    {
        "key": "p1",
        "name": "主角A",
        "gender": "男",
        "age": 20,
        "level": 10,
        "sect_id": 1,
        "technique_id": 10,
        "weapon_id": 100,
        "auxiliary_id": 200,
        "personas": [1, 2],
        "appearance": 5,
        "relations": "p2:lover;p3:friend"
    },
    {
        "key": "p2",
        "name": "主角B",
        "gender": "女",
        "age": 18,
        "level": 12,
        "sect_id": 1,
        "technique_id": 11,
        "weapon_id": 101,
        "auxiliary_id": 201,
        "personas": [3],
        "appearance": 6,
        "relations": "" # 单向测试，依赖 p1 的 relations 定义
    },
    {
        "key": "p3",
        "name": "主角C",
        "gender": "男",
        "age": 25,
        "level": 15,
        "sect_id": 2,
        "technique_id": 12,
        "weapon_id": 102,
        "auxiliary_id": 202,
        "personas": [],
        "appearance": 4,
        "relations": "p2:child" # p3 认 p2 为子女 (不再与 p1 冲突)
    },
    {
        "key": "p4",
        "name": "主角D",
        "gender": "女",
        "age": 22,
        "level": 11,
        "sect_id": 2,
        "technique_id": 13,
        "weapon_id": 103,
        "auxiliary_id": 203,
        "personas": [],
        "appearance": 7,
        "relations": "p1:enemy" # p4 视 p1 为仇敌 (测试 Enemy 关系)
    }
]

@pytest.fixture
def mock_game_configs():
    """
    Mock game_configs 字典，注入我们的测试数据。
    注意：spawn_protagonists 内部使用的是 src.utils.df.game_configs
    我们需要 patch 这个对象。
    """
    with patch("src.utils.protagonist.game_configs", {"protagonist": MOCK_PROTAGONIST_CONFIG}):
        yield

def test_spawn_basic_properties(base_world, mock_game_configs):
    """验证基本属性是否正确映射"""
    month = create_month_stamp(Year(100), Month.JANUARY)
    
    # 执行生成
    # probability=1.0 确保必然生成
    avatars_dict = spawn_protagonists(base_world, month, probability=1.0)
    
    assert len(avatars_dict) == 4
    
    # 验证 P1 (主角A) 的属性
    # 我们无法直接通过 key 获取（因为返回的是 id->avatar），需要遍历查找
    p1 = next((a for a in avatars_dict.values() if a.name == "主角A"), None)
    assert p1 is not None
    
    # 使用 Gender 枚举进行比较
    assert p1.gender == Gender.MALE
    assert p1.age.age == 20
    assert p1.cultivation_progress.level == 10
    assert p1.sect.id == 1
    
    # 验证 P2 (主角B)
    p2 = next((a for a in avatars_dict.values() if a.name == "主角B"), None)
    assert p2 is not None
    assert p2.gender == Gender.FEMALE
    assert p2.age.age == 18

def test_spawn_relations(base_world, mock_game_configs):
    """验证关系绑定逻辑"""
    month = create_month_stamp(Year(100), Month.JANUARY)
    avatars_dict = spawn_protagonists(base_world, month, probability=1.0)
    
    # 获取 Avatar 对象
    p1 = next(a for a in avatars_dict.values() if a.name == "主角A")
    p2 = next(a for a in avatars_dict.values() if a.name == "主角B")
    p3 = next(a for a in avatars_dict.values() if a.name == "主角C")
    p4 = next(a for a in avatars_dict.values() if a.name == "主角D")
    
    # -------------------------------------------
    # 验证 P1 配置: "p2:lover;p3:friend"
    # -------------------------------------------
    
    # 1. Lover 关系 (通常是双向的，但 become_lovers_with 可能会处理双向)
    # 检查 p1 的关系列表中是否有 p2，且类型为 LOVER
    # 注意：Avatar.get_relation 接受 Avatar 对象，返回 Relation 枚举
    p1_p2_relation = p1.get_relation(p2)
    assert p1_p2_relation == Relation.IS_LOVER
    
    # 检查 p2 的关系列表中是否有 p1 (双向验证)
    p2_p1_relation = p2.get_relation(p1)
    assert p2_p1_relation == Relation.IS_LOVER

    # 2. Friend 关系
    p1_p3_relation = p1.get_relation(p3)
    assert p1_p3_relation == Relation.IS_FRIEND
    
    # -------------------------------------------
    # 验证 P3 配置: "p2:child"
    # -------------------------------------------
    
    # 3. Enemy 关系 (现在由 p4 测试)
    # p4 视 p1 为敌人
    p4_p1_relation = p4.get_relation(p1)
    assert p4_p1_relation == Relation.IS_ENEMY

    # 检查反向关系 (Enemy 是对称的)
    p1_p4_relation = p1.get_relation(p4)
    assert p1_p4_relation == Relation.IS_ENEMY
    
    # 4. Child 关系 (Parent-Child)
    # 配置: p3 "p2:child" -> p3 acknowledge child p2 -> p3 是 p2 的长辈 (Parent)
    # 所以 p3 -> p2 是 CHILD (Relation.IS_CHILD 表示 "对方是我的孩子")
    # p2 -> p3 是 PARENT (Relation.IS_PARENT 表示 "对方是我的父母")
    
    p3_p2_relation = p3.get_relation(p2)
    # 注意：根据 acknowledge_child 实现，主语(p3)添加 CHILD 关系指向对象(p2)
    assert p3_p2_relation == Relation.IS_CHILD
    
    p2_p3_relation = p2.get_relation(p3)
    assert p2_p3_relation == Relation.IS_PARENT

def test_spawn_probability(base_world, mock_game_configs):
    """验证概率参数生效"""
    month = create_month_stamp(Year(100), Month.JANUARY)
    
    # 概率 0.0 -> 不应该生成任何角色
    avatars_dict = spawn_protagonists(base_world, month, probability=0.0)
    assert len(avatars_dict) == 0

def test_spawn_exception_handling(base_world):
    """验证当生成过程发生异常时是否能优雅降级（不崩溃并跳过该角色）"""
    
    BAD_CONFIG = [{
        "key": "bad_p1",
        "name": "坏数据主角",
    }]
    
    with patch("src.utils.protagonist.game_configs", {"protagonist": BAD_CONFIG}):
        # Mock create_avatar_from_request 抛出异常
        with patch("src.utils.protagonist.create_avatar_from_request", side_effect=Exception("Mock Creation Error")):
            month = create_month_stamp(Year(100), Month.JANUARY)
            
            # 应该不抛出异常，返回空字典
            avatars_dict = spawn_protagonists(base_world, month, probability=1.0)
            
            # 结果应该是没有生成该角色（被 try-except 捕获）
            assert len(avatars_dict) == 0
