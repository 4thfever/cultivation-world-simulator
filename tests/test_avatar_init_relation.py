import pytest
from src.classes.core.world import World
from src.systems.time import MonthStamp
from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.relation.relation import NumericRelation, Relation, get_relation_label
from src.systems.cultivation import CultivationProgress, Realm
from src.utils.id_generator import get_avatar_id
from src.sim.avatar_init import create_random_mortal, MortalPlanner, AvatarFactory, PopulationPlanner
from src.classes.core.sect import sects_by_id
import src.sim.avatar_init as avatar_init_module

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


def test_population_planner_can_generate_small_family_cluster(monkeypatch):
    """家庭规划应支持一个家长对应多个子女。"""
    monkeypatch.setattr(avatar_init_module, "FAMILY_TRIGGER_PROB", 1.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_PAIR_CAP_DIV", 4)
    monkeypatch.setattr(avatar_init_module, "FAMILY_CHILDREN_MAX", 3)

    found_cluster = False
    for _ in range(20):
        plan = PopulationPlanner.plan_group(24, existed_sects=None)
        child_count_by_parent: dict[int, int] = {}
        for (parent_idx, child_idx), relation in plan.relations.items():
            if relation is not Relation.IS_CHILD_OF:
                continue
            child_count_by_parent[parent_idx] = child_count_by_parent.get(parent_idx, 0) + 1
        if any(count >= 2 for count in child_count_by_parent.values()):
            found_cluster = True
            break

    assert found_cluster, "未生成任何一个家长对应多个子女的小家庭簇"


def test_family_members_do_not_overconcentrate_in_one_sect(monkeypatch):
    """同一小家庭落在同一宗门的人数不应超过上限。"""
    monkeypatch.setattr(avatar_init_module, "FAMILY_TRIGGER_PROB", 1.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_PAIR_CAP_DIV", 4)
    monkeypatch.setattr(avatar_init_module, "FAMILY_CHILDREN_MAX", 3)
    monkeypatch.setattr(avatar_init_module, "FAMILY_PARENT_SECT_FOLLOW_PROB", 1.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_OTHER_SECT_PROB", 0.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_SAME_SECT_CAP", 2)

    plan = PopulationPlanner.plan_group(30, existed_sects=list(sects_by_id.values()))

    family_members: dict[int, list[int]] = {}
    for (parent_idx, child_idx), relation in plan.relations.items():
        if relation is not Relation.IS_CHILD_OF:
            continue
        family_members.setdefault(parent_idx, [parent_idx]).append(child_idx)

    assert family_members, "未生成家庭关系，无法验证宗门分散规则"

    for members in family_members.values():
        sect_counts: dict[int, int] = {}
        for idx in members:
            sect = plan.sects[idx]
            if sect is None:
                continue
            sect_counts[sect.id] = sect_counts.get(sect.id, 0) + 1
        if sect_counts:
            assert max(sect_counts.values()) <= avatar_init_module.FAMILY_SAME_SECT_CAP, (
                f"家庭成员宗门过于集中: {sect_counts}"
            )


def test_population_planner_generates_denser_initial_relations():
    """开局关系应有一定密度，且应出现少量多关系角色。"""
    relation_coverage_ratios: list[float] = []
    multi_relation_ratios: list[float] = []

    for seed in range(10):
        avatar_init_module.random.seed(seed)
        plan = PopulationPlanner.plan_group(80, existed_sects=list(sects_by_id.values()))

        direct_relation_counts = [0] * 80
        for a_idx, b_idx in plan.relations.keys():
            direct_relation_counts[a_idx] += 1
            direct_relation_counts[b_idx] += 1

        covered_count = sum(1 for count in direct_relation_counts if count >= 1)
        multi_relation_count = sum(1 for count in direct_relation_counts if count >= 2)
        relation_coverage_ratios.append(covered_count / 80)
        multi_relation_ratios.append(multi_relation_count / 80)

    avg_coverage_ratio = sum(relation_coverage_ratios) / len(relation_coverage_ratios)
    avg_multi_ratio = sum(multi_relation_ratios) / len(multi_relation_ratios)

    assert avg_coverage_ratio >= 0.50, f"开局有直接关系的角色占比偏低: {avg_coverage_ratio:.3f}"
    assert avg_multi_ratio >= 0.12, f"开局拥有多个直接关系的角色占比偏低: {avg_multi_ratio:.3f}"


def test_build_group_lovers_start_with_friendliness(monkeypatch, mock_world):
    """道侣初始化后不应还是陌生人。"""
    monkeypatch.setattr(avatar_init_module, "LOVERS_TRIGGER_PROB", 1.0)
    monkeypatch.setattr(avatar_init_module, "LOVERS_PAIR_CAP_DIV", 1)
    monkeypatch.setattr(avatar_init_module, "MASTER_PAIR_PROB", 0.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_TRIGGER_PROB", 0.0)

    plan = PopulationPlanner.plan_group(2, existed_sects=None)
    avatars = list(AvatarFactory.build_group(mock_world, mock_world.month_stamp, plan).values())
    assert len(avatars) == 2

    lover_pairs = [
        (a, b)
        for a in avatars
        for b in avatars
        if a is not b and a.get_relation(b) == Relation.IS_LOVER_OF
    ]
    assert lover_pairs, "未生成道侣对，无法验证初始友好度"

    avatar_a, avatar_b = lover_pairs[0]
    assert avatar_a.get_friendliness(avatar_b) >= 25
    assert avatar_b.get_friendliness(avatar_a) >= 25
    assert avatar_a.get_numeric_relation(avatar_b) in {NumericRelation.FRIEND, NumericRelation.BEST_FRIEND}
    assert avatar_b.get_numeric_relation(avatar_a) in {NumericRelation.FRIEND, NumericRelation.BEST_FRIEND}


def test_population_planner_generates_numeric_relations_from_friendliness(monkeypatch, mock_world):
    """朋友/仇人等初始数值关系应从友好度自然推导，而不是显式规划。"""
    monkeypatch.setattr(avatar_init_module, "LOVERS_TRIGGER_PROB", 0.0)
    monkeypatch.setattr(avatar_init_module, "MASTER_PAIR_PROB", 0.0)
    monkeypatch.setattr(avatar_init_module, "FAMILY_TRIGGER_PROB", 0.0)
    monkeypatch.setattr(avatar_init_module, "INITIAL_FRIENDLINESS_PAIR_CAP_DIV", 1)

    plan = PopulationPlanner.plan_group(12, existed_sects=None)
    assert all(rel not in {Relation.IS_FRIEND_OF, Relation.IS_ENEMY_OF} for rel in plan.relations.values())

    avatars = list(AvatarFactory.build_group(mock_world, mock_world.month_stamp, plan).values())
    non_stranger_pairs = []
    for avatar in avatars:
        for target in avatars:
            if avatar is target:
                continue
            numeric_relation = avatar.get_numeric_relation(target)
            if numeric_relation != NumericRelation.STRANGER:
                non_stranger_pairs.append((avatar, target, numeric_relation))

    assert non_stranger_pairs, "未从初始友好度中推导出任何数值关系"


def test_same_sect_pairs_are_more_often_positive(monkeypatch, mock_world):
    """同宗门角色应更容易生成正向初始关系。"""
    sects = list(sects_by_id.values())
    assert len(sects) >= 2

    def make_avatar(name: str, sect, level: int) -> Avatar:
        return Avatar(
            world=mock_world,
            name=name,
            id=get_avatar_id(),
            birth_month_stamp=MonthStamp(0),
            age=Age(30, CultivationProgress(level).realm),
            gender=Gender.MALE,
            cultivation_progress=CultivationProgress(level),
            pos_x=0,
            pos_y=0,
            sect=sect,
        )

    same_a = make_avatar("SameA", sects[0], 30)
    same_b = make_avatar("SameB", sects[0], 32)
    diff_a = make_avatar("DiffA", sects[0], 30)
    diff_b = make_avatar("DiffB", sects[1], 70)

    same_positive = 0
    diff_positive = 0
    samples = 200

    for seed in range(samples):
        avatar_init_module.random.seed(seed)
        a_to_b, b_to_a = avatar_init_module._roll_social_initial_friendliness_pair(same_a, same_b)
        if a_to_b > 0 or b_to_a > 0:
            same_positive += 1

        avatar_init_module.random.seed(seed)
        a_to_b, b_to_a = avatar_init_module._roll_social_initial_friendliness_pair(diff_a, diff_b)
        if a_to_b > 0 or b_to_a > 0:
            diff_positive += 1

    assert same_positive > diff_positive
