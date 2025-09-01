import random
from src.classes.calendar import Month, Year, MonthStamp
from src.classes.cultivation import Realm

class Age:
    """
    角色寿命管理
    基于境界计算期望寿命，超过期望寿命后有概率老死
    """
    
    # 各境界的基础期望寿命（年）
    # REALM_LIFESPAN = {
    #     Realm.Qi_Refinement: 100,      # 练气期：100年
    #     Realm.Foundation_Establishment: 200,  # 筑基期：200年
    #     Realm.Core_Formation: 500,      # 金丹期：500年
    #     Realm.Nascent_Soul: 1000,      # 元婴期：1000年
    # }
    REALM_LIFESPAN = {
        Realm.Qi_Refinement: 50,      # 练气期：100年
        Realm.Foundation_Establishment: 60,  # 筑基期：200年
        Realm.Core_Formation: 70,      # 金丹期：500年
        Realm.Nascent_Soul: 80,      # 元婴期：1000年
    }
    
    def __init__(self, age: int):
        self.age = age
    
    def get_age(self) -> int:
        """获取当前年龄"""
        return self.age
    
    def get_expected_lifespan(self, realm: Realm) -> int:
        """获取期望寿命"""
        return self.REALM_LIFESPAN.get(realm, 100)
    
    def get_death_probability(self, realm: Realm) -> float:
        """
        计算当月老死的概率
        
        返回:
            老死概率，范围0.0-0.1
        """
        if self.age < self.get_expected_lifespan(realm):
            return 0.0
        
        # 超过期望寿命的年数
        years_over_lifespan = self.age - self.get_expected_lifespan(realm)
        
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
    
    def __str__(self) -> str:
        """返回年龄的字符串表示"""
        return str(self.age)
    
    def __repr__(self) -> str:
        """返回年龄的详细字符串表示"""
        return f"Age({self.age})"
