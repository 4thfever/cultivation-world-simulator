"""测试 new_avatar 模块的角色创建逻辑."""
import pytest
from src.sim.avatar_init import make_avatars, AvatarFactory, PopulationPlanner
from src.classes.age import Age
from src.systems.cultivation import CultivationProgress
from src.classes.relation.relation import Relation
from src.classes.core.sect import sects_by_id


class TestAgeLifespanConstraint:
    """测试角色创建时年龄不超过寿命上限的约束."""

    def test_batch_creation_age_within_lifespan(self, base_world):
        """批量创建角色时，年龄应不超过境界寿命上限.

        注意：只有当随机生成的年龄 >= 寿命上限时才会触发调整，
        调整后的年龄会在 80%-95% 区间内。正常随机生成的年龄
        （如 77 岁 / 80 寿命）不会被调整，所以可能接近但不超过上限。
        """
        # 创建大量角色以增加覆盖率
        avatars = make_avatars(base_world, count=100)

        for avatar in avatars.values():
            max_lifespan = Age.REALM_LIFESPAN.get(
                avatar.cultivation_progress.realm, 100
            )
            assert avatar.age.age < max_lifespan, (
                f"角色 {avatar.name} 年龄 {avatar.age.age} 超过了"
                f"境界 {avatar.cultivation_progress.realm} 的寿命上限 {max_lifespan}"
            )

    def test_batch_creation_no_immediate_death(self, base_world):
        """批量创建的角色不应该一出生就处于必死状态.
        
        注：新机制下，大限前20年会有死亡概率，所以不能断言概率为0，
        只能断言概率不为1.0（即没死透）。
        """
        avatars = make_avatars(base_world, count=100)

        for avatar in avatars.values():
            death_prob = avatar.age.get_death_probability()
            
            # 1. 刚生成的活人角色不应该必死
            assert death_prob < 1.0, (
                f"角色 {avatar.name} 刚生成就必死 (prob={death_prob})"
            )
            
            # 2. 如果在安全期，概率应为0
            safe_limit = avatar.age.max_lifespan - 20
            if avatar.age.age < safe_limit:
                assert death_prob == 0.0, (
                    f"角色 {avatar.name} 处于安全期 ({avatar.age.age}/{safe_limit}) "
                    f"却有老死概率 {death_prob}"
                )

    def test_multiple_batch_creations_consistent(self, base_world):
        """多次批量创建应该都满足年龄约束."""
        for _ in range(5):
            avatars = make_avatars(base_world, count=50)
            for avatar in avatars.values():
                max_lifespan = Age.REALM_LIFESPAN.get(
                    avatar.cultivation_progress.realm, 100
                )
                assert avatar.age.age < max_lifespan


class TestRealmLifespanMapping:
    """测试各境界的寿命上限映射."""

    def test_qi_refinement_lifespan(self, base_world):
        """练气期角色年龄应不超过100岁."""
        from src.systems.cultivation import Realm

        avatars = make_avatars(base_world, count=100)
        qi_refinement_avatars = [
            av for av in avatars.values()
            if av.cultivation_progress.realm == Realm.Qi_Refinement
        ]

        # 获取当前配置的寿命
        limit = Age.REALM_LIFESPAN[Realm.Qi_Refinement]
        
        for avatar in qi_refinement_avatars:
            assert avatar.age.age < limit, (
                f"练气期角色 {avatar.name} 年龄 {avatar.age.age} 超过 {limit}"
            )

    def test_foundation_establishment_lifespan(self, base_world):
        """筑基期角色年龄应不超过150岁."""
        from src.systems.cultivation import Realm

        avatars = make_avatars(base_world, count=100)
        fe_avatars = [
            av for av in avatars.values()
            if av.cultivation_progress.realm == Realm.Foundation_Establishment
        ]

        # 获取当前配置的寿命
        limit = Age.REALM_LIFESPAN[Realm.Foundation_Establishment]

        for avatar in fe_avatars:
            assert avatar.age.age < limit, (
                f"筑基期角色 {avatar.name} 年龄 {avatar.age.age} 超过 {limit}"
            )


class TestInitialRelationConstraints:
    """测试开局批量生成时的关系约束."""

    def test_batch_creation_parent_child_constraints(self, base_world):
        """亲子关系应满足年龄和等级差约束."""
        for _ in range(10):
            avatars = make_avatars(base_world, count=80)
            for avatar in avatars.values():
                for other, relation in avatar.relations.items():
                    if relation is not Relation.IS_CHILD_OF:
                        continue
                    assert avatar.age.age - other.age.age >= 16, (
                        f"父母 {avatar.name}({avatar.age.age}) 与子女 "
                        f"{other.name}({other.age.age}) 年龄差不合法"
                    )
                    assert avatar.cultivation_progress.level - other.cultivation_progress.level >= 10, (
                        f"父母 {avatar.name}({avatar.cultivation_progress.level}) 与子女 "
                        f"{other.name}({other.cultivation_progress.level}) 等级差不合法"
                    )

    def test_batch_creation_master_disciple_constraints(self, base_world):
        """师徒关系应满足等级差约束."""
        sects = list(sects_by_id.values())
        for _ in range(10):
            avatars = make_avatars(base_world, count=80, existed_sects=sects)
            found_master_pair = False
            for avatar in avatars.values():
                for other, relation in avatar.relations.items():
                    if relation is not Relation.IS_DISCIPLE_OF:
                        continue
                    found_master_pair = True
                    assert avatar.cultivation_progress.level - other.cultivation_progress.level >= 20, (
                        f"师傅 {avatar.name}({avatar.cultivation_progress.level}) 与徒弟 "
                        f"{other.name}({other.cultivation_progress.level}) 等级差不合法"
                    )
            if found_master_pair:
                break
        else:
            pytest.skip("本轮随机未生成师徒关系，跳过约束断言")

    def test_batch_creation_cultivation_start_not_in_future(self, base_world):
        """所有初始角色的修炼开始时间都不应晚于当前时间."""
        avatars = make_avatars(base_world, count=120, current_month_stamp=base_world.month_stamp)
        current_month = int(base_world.month_stamp)
        for avatar in avatars.values():
            assert avatar.cultivation_start_month_stamp is not None
            assert int(avatar.cultivation_start_month_stamp) <= current_month, (
                f"角色 {avatar.name} 的修炼开始时间 "
                f"{int(avatar.cultivation_start_month_stamp)} 晚于当前时间 {current_month}"
            )
