from src.classes.age import Age


class TestAgeDeathMechanic:
    """测试新的寿元与即时死亡机制。"""

    def test_alive_before_lifespan_limit(self):
        age = Age(50, innate_max_lifespan=80)
        age.recalculate_max_lifespan(extra_bonus=20)

        assert age.max_lifespan == 100
        assert age.get_death_probability() == 0.0
        assert age.death_by_old_age() is False

    def test_die_immediately_at_lifespan_limit(self):
        age = Age(100, innate_max_lifespan=80)
        age.recalculate_max_lifespan(extra_bonus=20)

        assert age.max_lifespan == 100
        assert age.get_death_probability() == 1.0

    def test_negative_lifespan_effect_can_cause_immediate_death(self):
        age = Age(79, innate_max_lifespan=80)
        age.recalculate_max_lifespan(extra_bonus=5)
        assert age.max_lifespan == 85

        age.recalculate_max_lifespan(extra_bonus=-5)
        assert age.max_lifespan == 75
        assert age.get_death_probability() == 1.0

    def test_innate_lifespan_change_updates_runtime_lifespan(self):
        age = Age(50, innate_max_lifespan=70)
        age.recalculate_max_lifespan(extra_bonus=10)
        assert age.max_lifespan == 80

        age.increase_max_lifespan(5)
        assert age.innate_max_lifespan == 75
        assert age.max_lifespan == 85

        age.decrease_max_lifespan(10)
        assert age.innate_max_lifespan == 65
        assert age.max_lifespan == 75
