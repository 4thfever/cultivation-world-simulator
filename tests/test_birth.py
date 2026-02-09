import pytest
import copy
from unittest.mock import patch, MagicMock
from src.classes.relation.relation import Relation
from src.classes.core.avatar import Gender
from src.utils.config import CONFIG
from src.sim.simulator import Simulator
from src.systems.time import MonthStamp

def test_couple_birth_logic(base_world, dummy_avatar):
    """
    测试道侣生子逻辑：
    1. 建立关系
    2. 检查时间限制
    3. 检查触发生成
    4. 检查数量限制
    """
    # 1. 准备父母
    father = dummy_avatar
    father.gender = Gender.MALE
    father.name = "张三"
    
    # 注册 father 到 avatar_manager
    base_world.avatar_manager.register_avatar(father)
    
    # 创建 mother
    mother = copy.deepcopy(dummy_avatar)
    mother.id = "mother_id"
    mother.gender = Gender.FEMALE
    mother.name = "李四"
    # 清空可能复制过来的数据
    mother.children = []
    mother.relation_start_dates = {}
    mother.relations = {}
    
    base_world.avatar_manager.register_avatar(mother)
    
    # 2. 建立关系并回溯时间
    father.become_lovers_with(mother)
    
    # 验证关系建立时记录了时间
    current_time = int(base_world.month_stamp)
    assert father.relation_start_dates[mother.id] == current_time
    assert mother.relation_start_dates[father.id] == current_time
    
    # 手动修改开始时间为 13 个月前，以满足 > 12 个月的条件
    start_time = current_time - 13
    father.relation_start_dates[mother.id] = start_time
    mother.relation_start_dates[father.id] = start_time
    
    # 3. Mock 配置和概率，确保必中
    CONFIG.game.birth_rate_per_month = 1.0 
    CONFIG.game.max_children_per_couple = 1
    
    # 4. 运行模拟器步骤
    sim = Simulator(base_world)
    
    # 第一次运行，应该生一个
    # 确保 awakening_rate 为 0 避免干扰
    sim.awakening_rate = 0
    
    with patch("random.random", return_value=0.0): # 确保概率判定通过
        living_avatars = base_world.avatar_manager.get_living_avatars()
        events = sim._phase_update_age_and_birth(living_avatars)
        
    # 5. 验证生成结果
    assert len(father.children) == 1
    child = father.children[0]
    
    # 验证姓名：随父姓 (张)
    assert child.name.startswith("张")
    
    # 验证双向绑定
    assert child in mother.children
    assert str(father.id) in child.parents
    assert str(mother.id) in child.parents
    
    # 验证事件
    # 兼容中英文环境
    birth_events = [e for e in events if "gave birth to a" in str(e) or "诞下" in str(e)]
    assert len(birth_events) > 0
    
    # 6. 验证上限 (再次运行不应新增，因为 max_children_per_couple = 1)
    with patch("random.random", return_value=0.0):
        living_avatars = base_world.avatar_manager.get_living_avatars()
        sim._phase_update_age_and_birth(living_avatars)
        
    assert len(father.children) == 1
    
def test_birth_time_restriction(base_world, dummy_avatar):
    """
    测试时间限制：关系不满一年不生
    """
    father = dummy_avatar
    base_world.avatar_manager.register_avatar(father)
    
    mother = copy.deepcopy(dummy_avatar)
    mother.id = "mother_id_2"
    base_world.avatar_manager.register_avatar(mother)
    
    father.become_lovers_with(mother)
    
    # 此时时间刚刚建立，不满一年
    CONFIG.game.birth_rate_per_month = 1.0
    sim = Simulator(base_world)
    sim.awakening_rate = 0
    
    with patch("random.random", return_value=0.0):
        living_avatars = base_world.avatar_manager.get_living_avatars()
        sim._phase_update_age_and_birth(living_avatars)
        
    assert len(father.children) == 0

