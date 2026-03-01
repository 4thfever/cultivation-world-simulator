import pytest
from src.classes.relation.relation import Relation, is_innate
from src.classes.relation.relations import get_possible_new_relations, cancel_relation
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm, CultivationProgress
from src.systems.time import MonthStamp
from src.utils.id_generator import get_avatar_id

@pytest.fixture
def base_avatars(base_world):
    """
    提供一组用于测试的基础角色，等级和性别不同。
    """
    def _create(name, gender, level):
        return Avatar(
            world=base_world,
            name=name,
            id=get_avatar_id(),
            birth_month_stamp=MonthStamp(0),
            age=Age(20, CultivationProgress(level).realm),
            gender=gender,
            cultivation_progress=CultivationProgress(level),
            pos_x=0, pos_y=0
        )
    
    male_low = _create("MaleLow", Gender.MALE, 10)
    female_low = _create("FemaleLow", Gender.FEMALE, 10)
    male_high = _create("MaleHigh", Gender.MALE, 50) # Level 50 > 10 + 20
    female_high = _create("FemaleHigh", Gender.FEMALE, 50)
    
    return {
        "male_low": male_low,
        "female_low": female_low,
        "male_high": male_high,
        "female_high": female_high
    }

def test_relation_rules_lovers(base_avatars):
    """
    测试道侣关系的建立规则：
    1. 异性可以结为道侣 (IS_LOVER_OF)
    2. 同性不可结为道侣
    3. 已是道侣则不再出现在候选列表中
    """
    m = base_avatars["male_low"]
    f = base_avatars["female_low"]
    m2 = base_avatars["male_high"]
    
    # 1. 异性
    # f 相对于 m 的可能关系
    candidates = get_possible_new_relations(m, f)
    assert Relation.IS_LOVER_OF in candidates
    
    # 2. 同性
    candidates_same = get_possible_new_relations(m, m2)
    assert Relation.IS_LOVER_OF not in candidates_same
    
    # 3. 已存在
    m.become_lovers_with(f)
    candidates_exist = get_possible_new_relations(m, f)
    assert Relation.IS_LOVER_OF not in candidates_exist

def test_relation_rules_master(base_avatars):
    """
    测试拜师关系的等级限制 (MASTER)：
    1. 对方等级 >= 己方 + 20：可以拜师 (IS_MASTER_OF)
    2. 对方等级 < 己方 + 20：不可拜师
    """
    low = base_avatars["male_low"]   # Lv 10
    high = base_avatars["male_high"] # Lv 50
    
    # 1. 拜师 (high 是 low 的师傅?)
    # get_possible_new_relations(from, to) 返回的是 to 相对于 from 的关系
    # 即：检查 high 是否可以是 low 的 MASTER
    candidates = get_possible_new_relations(low, high)
    assert Relation.IS_MASTER_OF in candidates
    
    # 2. 等级不足 (low 是 high 的师傅?) -> 不可能
    candidates_rev = get_possible_new_relations(high, low)
    assert Relation.IS_MASTER_OF not in candidates_rev

def test_relation_rules_disciple(base_avatars):
    """
    测试收徒关系的等级限制 (DISCIPLE)：
    1. 对方等级 <= 己方 - 20：可以收徒 (IS_DISCIPLE_OF)
    2. 对方等级 > 己方 - 20：不可收徒
    """
    low = base_avatars["male_low"]   # Lv 10
    high = base_avatars["male_high"] # Lv 50
    
    # 1. 收徒 (low 是 high 的徒弟?)
    # get_possible_new_relations(from, to) -> to 是 from 的 ???
    # 检查 low 是否可以是 high 的 DISCIPLE
    candidates = get_possible_new_relations(high, low)
    assert Relation.IS_DISCIPLE_OF in candidates
    
    # 2. 等级过高 (high 是 low 的徒弟?) -> 不可能
    candidates_rev = get_possible_new_relations(low, high)
    assert Relation.IS_DISCIPLE_OF not in candidates_rev

def test_relation_reciprocal_consistency(base_avatars):
    """
    测试新语义方法的双向一致性：
    1. A acknowledge_master(B) -> A存 IS_MASTER_OF, B存 IS_DISCIPLE_OF
    2. A acknowledge_parent(B) -> A存 IS_PARENT, B存 IS_CHILD_OF
    3. A make_friend_with(B) -> 双方都存 IS_FRIEND_OF
    """
    a = base_avatars["male_low"]
    b = base_avatars["female_high"]
    
    # 1. Master/Disciple
    a.acknowledge_master(b)
    assert a.get_relation(b) == Relation.IS_MASTER_OF
    assert b.get_relation(a) == Relation.IS_DISCIPLE_OF
    
    # 清理
    a.clear_relation(b)
    assert a.get_relation(b) is None
    
    # 2. Parent/Child
    a.acknowledge_parent(b)
    assert a.get_relation(b) == Relation.IS_PARENT_OF
    assert b.get_relation(a) == Relation.IS_CHILD_OF
    
    a.clear_relation(b)
    
    # 3. Friend (Symmetric)
    a.make_friend_with(b)
    assert a.get_relation(b) == Relation.IS_FRIEND_OF
    assert b.get_relation(a) == Relation.IS_FRIEND_OF

def test_relation_cancel_rules(base_avatars):
    """
    测试关系取消规则：
    1. 后天关系（如朋友、师徒）可以取消
    2. 先天关系（如父母、子女）不可取消
    """
    a = base_avatars["male_low"]
    b = base_avatars["female_high"]
    
    # 1. 后天关系 (Friend)
    a.make_friend_with(b)
    success = cancel_relation(a, b, Relation.IS_FRIEND_OF)
    assert success is True
    assert a.get_relation(b) is None
    
    # 2. 先天关系 (Parent)
    # 先验证 PARENT 是先天关系
    assert is_innate(Relation.IS_PARENT_OF) is True
    
    a.acknowledge_parent(b)
    success = cancel_relation(a, b, Relation.IS_PARENT_OF)
    assert success is False # 应该失败
    assert a.get_relation(b) == Relation.IS_PARENT_OF # 关系依然存在

def test_relation_rules_desc_contains_all_rules():
    """
    测试获取关系规则描述的函数是否正确包含了所有的规则翻译，
    确保不会因为缺少翻译（原样返回英文 ID）而漏失信息。
    """
    from src.classes.relation.relation import get_relation_rules_desc, ADD_RELATION_RULES, CANCEL_RELATION_RULES
    
    desc = get_relation_rules_desc()
    
    # 所有的关系建立和解除规则，都应该被翻译成非全英文 id 的形式
    # get_relation_rules_desc 内部调用了 t() 进行翻译
    for rel, msgid in ADD_RELATION_RULES.items():
        assert msgid not in desc, f"翻译缺失或描述中未包含建立规则翻译：{msgid}"
        
    for rel, msgid in CANCEL_RELATION_RULES.items():
        assert msgid not in desc, f"翻译缺失或描述中未包含解除规则翻译：{msgid}"
