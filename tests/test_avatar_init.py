"""测试 new_avatar 模块的角色创建逻辑."""
import pytest

from src.classes.relation.relation import Relation
from src.classes.core.sect import sects_by_id
from src.i18n import t
from src.sim.avatar_init import make_avatars


class TestAgeLifespanInitialization:
    """测试新角色的先天寿元与即时死亡规则。"""

    def test_batch_creation_innate_lifespan_within_range(self, base_world):
        avatars = make_avatars(base_world, count=100)

        for avatar in avatars.values():
            assert 60 <= avatar.age.innate_max_lifespan <= 90

    def test_batch_creation_can_include_immediately_dead_avatars(self, base_world):
        avatars = make_avatars(base_world, count=120)

        dead_found = False
        for avatar in avatars.values():
            if avatar.age.age >= avatar.age.max_lifespan:
                assert avatar.is_dead is True
                dead_found = True

        assert dead_found is True

    def test_batch_creation_living_avatar_not_over_limit(self, base_world):
        avatars = make_avatars(base_world, count=120)

        for avatar in avatars.values():
            if avatar.is_dead:
                continue
            assert avatar.age.age < avatar.age.max_lifespan

    def test_realm_bonus_participates_in_effects_breakdown(self, base_world):
        avatars = make_avatars(base_world, count=80)
        living = [avatar for avatar in avatars.values() if not avatar.is_dead]
        assert living

        avatar = living[0]
        breakdown = dict(avatar.get_effect_breakdown())
        realm_label = t("effect_source_cultivation_realm")
        assert realm_label in breakdown
        assert "extra_max_lifespan" in breakdown[realm_label]


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
