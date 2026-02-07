import pytest
from src.classes.age import Age
from src.systems.cultivation import Realm

class TestAgeDeathMechanic:
    """测试新的寿命与老死机制"""

    def test_safe_zone(self):
        """测试安全期：年龄 < 寿命上限 - 20"""
        # 练气期寿命 100
        age = Age(50, Realm.Qi_Refinement) 
        assert age.max_lifespan == 100
        
        # 50岁肯定安全
        assert age.get_death_probability() == 0.0
        
        # 79岁也安全 (100 - 20 = 80)
        age.age = 79
        assert age.get_death_probability() == 0.0

    def test_twilight_zone(self):
        """测试衰退期：寿命上限 - 20 <= 年龄 < 寿命上限"""
        # 练气期寿命 100，衰退期开始于 80
        age = Age(80, Realm.Qi_Refinement)
        
        # 刚进入衰退期
        prob_80 = age.get_death_probability()
        assert prob_80 == 0.0 # (80 - 80) * 0.005 = 0
        
        # 81岁
        age.age = 81
        prob_81 = age.get_death_probability()
        assert prob_81 > 0.0
        assert prob_81 == 0.005 # (81 - 80) * 0.005
        
        # 90岁
        age.age = 90
        prob_90 = age.get_death_probability()
        assert prob_90 == 0.05 # (90 - 80) * 0.005
        
        # 99岁
        age.age = 99
        prob_99 = age.get_death_probability()
        assert prob_99 > prob_90
        assert prob_99 < 1.0

    def test_doom_zone(self):
        """测试大限：年龄 >= 寿命上限"""
        age = Age(100, Realm.Qi_Refinement)
        
        # 刚好到达大限
        assert age.get_death_probability() == 1.0
        
        # 超过大限
        age.age = 101
        assert age.get_death_probability() == 1.0

    def test_realm_breakthrough_extends_life(self):
        """测试突破境界延长寿命，脱离危险区"""
        # 练气期 90岁 (寿命100)，处于危险区
        age = Age(90, Realm.Qi_Refinement)
        assert age.get_death_probability() > 0.0
        
        # 突破到筑基期 (寿命150)
        age.update_realm(Realm.Foundation_Establishment)
        assert age.max_lifespan == 150
        
        # 90岁对于150岁上限来说，远未到危险区 (150-20=130)
        assert age.get_death_probability() == 0.0

    def test_lifespan_reduction_items(self):
        """测试寿命上限减少导致提前进入危险区"""
        age = Age(50, Realm.Qi_Refinement)
        assert age.max_lifespan == 100
        
        # 遭受重创，折寿40年 -> 上限变60
        age.decrease_max_lifespan(40)
        assert age.max_lifespan == 60
        
        # 50岁对于60岁上限来说，已进入危险区 (60-20=40)
        assert age.get_death_probability() > 0.0
        # (50 - 40) * 0.005 = 0.05
        assert age.get_death_probability() == 0.05

