import random
from src.classes.calendar import Month, Year, MonthStamp
from src.classes.cultivation import Realm

class Age:
    """
    角色寿命管理
    基于境界计算期望寿命，超过期望寿命后有概率老死
    """
    
    # 各境界的基础期望寿命（年）
    REALM_LIFESPAN = {
        Realm.Qi_Refinement: 80,      # 练气期：100年
        Realm.Foundation_Establishment: 120,  # 筑基期：200年
        Realm.Core_Formation: 200,      # 金丹期：500年
        Realm.Nascent_Soul: 500,      # 元婴期：1000年
    }

    
    def __init__(self, age: int, realm: Realm):
        self.age = age
        # 最大理论寿元（年），初始化为 max(境界基线, 当前年龄+1)
        self.max_lifespan: int = max(self.get_base_expected_lifespan(realm), self.age + 1)
    
    def get_age(self) -> int:
        """获取当前年龄"""
        return self.age
    
    def get_expected_lifespan(self, realm: Realm) -> int:
        """获取期望寿命（即当前最大寿元上限）。"""
        return self.max_lifespan

    def get_base_expected_lifespan(self, realm: Realm) -> int:
        """获取境界对应的基线期望寿命（不受max_lifespan影响）。"""
        return self.REALM_LIFESPAN.get(realm, 100)

    def set_initial_max_lifespan(self, realm: Realm) -> None:
        """构造时已设置最大寿元，此处保持与构造策略一致。"""
        base = self.get_base_expected_lifespan(realm)
        self.max_lifespan = max(base, self.age + 1)

    def ensure_max_lifespan_at_least_realm_base(self, realm: Realm) -> None:
        """确保最大寿元至少达到 max(该境界基线, 当前年龄+1)。"""
        base = self.get_base_expected_lifespan(realm)
        floor_value = max(base, self.age + 1)
        if self.max_lifespan < floor_value:
            self.max_lifespan = floor_value

    def increase_max_lifespan(self, years: int) -> None:
        """提升最大寿元上限。"""
        if years <= 0:
            return
        self.max_lifespan = (self.max_lifespan or 0) + years

    def decrease_max_lifespan(self, years: int) -> None:
        """降低最大寿元上限（可以低于当前年龄）。"""
        if years <= 0:
            return
        self.max_lifespan = self.max_lifespan - years
    
    def get_death_probability(self, realm: Realm | None = None) -> float:
        """
        计算当月老死的概率
        
        返回:
            老死概率，范围0.0-0.1
        """
        expected = self.max_lifespan if realm is None else self.get_expected_lifespan(realm)
        if self.age < expected:
            return 0.0
        
        # 超过期望寿命的年数
        years_over_lifespan = self.age - expected
        
        # 基础概率：每超过1年增加0.01的概率
        death_probability = min(years_over_lifespan * 0.01, 0.1)

        return death_probability
        
    def death_by_old_age(self, realm: Realm) -> bool:
        """
        判断是否老死
        """
        return random.random() < self.get_death_probability(realm)


    
    def calculate_age(self, current_month_stamp: MonthStamp, birth_month_stamp: MonthStamp) -> int:
        """
        计算准确的年龄（整数年）
        
        Args:
            current_month_stamp: 当前时间戳
            birth_month_stamp: 出生时间戳
            
        Returns:
            整数年龄
        """
        return max(0, (current_month_stamp - birth_month_stamp) // 12)
    
    def update_age(self, current_month_stamp: MonthStamp, birth_month_stamp: MonthStamp):
        """
        更新年龄
        """
        self.age = self.calculate_age(current_month_stamp, birth_month_stamp)
    
    def get_lifespan_progress(self, realm: Realm | None = None) -> tuple[int, int]:
        """返回 (当前年龄, 期望寿命)。realm为空时使用当前最大寿元。"""
        expected = self.max_lifespan if realm is None else self.get_expected_lifespan(realm)
        return self.age, expected
    
    def is_elderly(self, realm: Realm | None = None) -> bool:
        """是否超过期望寿命。realm为空时使用当前最大寿元。"""
        expected = self.max_lifespan if realm is None else self.get_expected_lifespan(realm)
        return self.age >= expected
    
    def __str__(self) -> str:
        max_str = str(self.max_lifespan)
        return f"{self.age}/{max_str}"
    
    def __repr__(self) -> str:
        """返回年龄的详细字符串表示"""
        return f"Age({self.age})"
