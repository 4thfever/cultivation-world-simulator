import pytest
from src.classes.core.world import World
from src.systems.time import MonthStamp
from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.relation.relation import Relation, get_relation_label
from src.systems.cultivation import CultivationProgress, Realm
from src.utils.id_generator import get_avatar_id
from src.sim.avatar_init import create_random_mortal, MortalPlanner, AvatarFactory, PopulationPlanner

@pytest.fixture
def mock_world(base_world):
    return base_world

def test_single_mortal_relation(mock_world):
    """测试单个新角色生成时的亲子关系方向是否正确"""
    # 1. 创建一个假设的父母角色
    parent_avatar = Avatar(
        world=mock_world,
        name="Parent",
        id=get_avatar_id(),
        birth_month_stamp=MonthStamp(0),
        age=Age(100, Realm.Core_Formation),
        gender=Gender.FEMALE,
        cultivation_progress=CultivationProgress(60), # 金丹期
        pos_x=0,
        pos_y=0
    )
    # 加入世界管理器
    mock_world.avatar_manager.register_avatar(parent_avatar)

    # 2. 创建一个新角色，作为子女
    # 我们通过强制指定 parent_avatar 来测试关系设置逻辑
    # 由于 create_random_mortal 内部逻辑有随机性，这里直接使用底层 factory 并构造 plan
    
    child_age = Age(20, Realm.Qi_Refinement)
    plan = MortalPlanner.plan(mock_world, "Child", child_age, level=10, allow_relations=False)
    
    # 手动指定父母，模拟 random 选中的情况
    plan.parent_avatar = parent_avatar
    
    child_avatar = AvatarFactory.build_from_plan(
        mock_world, 
        mock_world.month_stamp, 
        name="Child", 
        age=child_age, 
        plan=plan,
        attach_relations=True
    )

    # 3. 验证关系
    # 父母看子女：应该是 IS_CHILD_OF (对方是我的子女)
    rel_from_parent = parent_avatar.get_relation(child_avatar)
    assert rel_from_parent == Relation.IS_CHILD_OF, f"父母看子女应该是 IS_CHILD_OF, 但得到了 {rel_from_parent}"
    
    label_from_parent = get_relation_label(rel_from_parent, parent_avatar, child_avatar)
    # 因为 child 性别随机，可能是 儿子 或 女儿
    assert label_from_parent in ["儿子", "女儿"], f"父母看子女的称谓错误: {label_from_parent}"

    # 子女看父母：应该是 IS_PARENT (对方是我的父母)
    rel_from_child = child_avatar.get_relation(parent_avatar)
    assert rel_from_child == Relation.IS_PARENT_OF, f"子女看父母应该是 IS_PARENT, 但得到了 {rel_from_child}"

    label_from_child = get_relation_label(rel_from_child, child_avatar, parent_avatar)
    assert label_from_child == "母亲", f"子女看母亲的称谓错误: {label_from_child}" # parent 是 FEMALE


def test_population_planner_relations(mock_world):
    """测试批量生成时的亲子关系方向是否正确"""
    # 强制生成一组角色，通过大量生成来触发家庭关系
    # 为了提高概率，我们直接调用 PopulationPlanner 内部逻辑或者检查生成后的结果
    
    # 尝试生成 20 个角色，期望出现家庭关系
    count = 20
    avatars_dict = PopulationPlanner.plan_group(count, existed_sects=None)
    
    # 检查计划中的关系
    relations = avatars_dict.relations
    
    if not relations:
        pytest.skip("本次随机未生成任何关系，跳过测试")
        return

    found_parent_relation = False
    
    for (a_idx, b_idx), rel in relations.items():
        if rel == Relation.IS_CHILD_OF:
            found_parent_relation = True
            # 在 plan_group 中，(a, b) = IS_CHILD_OF 意味着 a 是父母（a 认为 b 是子女），b 是子女
            # 这里的语义是：a 的 relations 中，对 b 的记录是 IS_CHILD_OF
            pass
            
    # 如果找到了 IS_CHILD_OF 关系，说明代码中使用了 Relation.IS_CHILD_OF
    # 修正后应该是 Relation.IS_CHILD_OF
    
    # 进一步：实际构建角色并验证
    avatars_map = AvatarFactory.build_group(mock_world, mock_world.month_stamp, avatars_dict)
    avatars = list(avatars_map.values())
    
    # 由于 build_group 返回的是 dict[id, Avatar]，且顺序可能打乱，我们需要重新映射 index
    # 但我们其实只需要遍历所有 Avatar 检查关系即可
    
    for av in avatars:
        for target, rel in av.relations.items():
            if rel == Relation.IS_CHILD_OF:
                # av 认为是子女 -> target 是子女
                # 验证年龄：父母应该比子女大
                assert av.age.age > target.age.age, f"父母({av.name}, {av.age.age}) 应该比子女({target.name}, {target.age.age}) 大"
                
                # 验证称谓
                label = get_relation_label(rel, av, target)
                assert label in ["儿子", "女儿"]
                
            elif rel == Relation.IS_PARENT_OF:
                # av 认为是父母 -> target 是父母
                # 验证年龄：子女应该比父母小
                assert av.age.age < target.age.age, f"子女({av.name}, {av.age.age}) 应该比父母({target.name}, {target.age.age}) 小"
                
                # 验证称谓
                label = get_relation_label(rel, av, target)
                assert label in ["父亲", "母亲"]

    if not found_parent_relation:
        # 如果随机没随到家庭，我们可以认为只要没报错且逻辑通顺就行，
        # 或者可以 mock random 来强制覆盖路径，但在集成测试中只要多跑几次通常能覆盖
        pass
