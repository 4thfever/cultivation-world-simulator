from typing import Dict, List, Optional
from src.classes.mortal import Mortal
from src.systems.time import MonthStamp

class MortalManager:
    """
    管理世界中的凡人（非修仙者）。
    负责凡人的存储、生命周期管理（老化、死亡）以及提供觉醒候选人。
    """
    def __init__(self):
        self.mortals: Dict[str, Mortal] = {}
        
    def register_mortal(self, mortal: Mortal) -> None:
        """注册一个新的凡人"""
        self.mortals[mortal.id] = mortal
        
    def remove_mortal(self, mortal_id: str) -> None:
        """移除凡人（觉醒或死亡）"""
        if mortal_id in self.mortals:
            del self.mortals[mortal_id]
            
    def get_mortal(self, mortal_id: str) -> Optional[Mortal]:
        return self.mortals.get(mortal_id)
        
    def get_awakening_candidates(self, current_month: MonthStamp, min_age: int = 16) -> List[Mortal]:
        """获取满足觉醒年龄条件的凡人列表"""
        candidates = []
        for mortal in self.mortals.values():
            age_months = int(current_month) - int(mortal.birth_month_stamp)
            age_years = age_months // 12
            if age_years >= min_age:
                candidates.append(mortal)
        return candidates

    def cleanup_dead_mortals(self, current_month: MonthStamp, max_lifespan: int = 80) -> int:
        """
        清理超过寿命上限的凡人。
        返回清理的数量。
        """
        dead_ids = []
        for mid, mortal in self.mortals.items():
             age_months = int(current_month) - int(mortal.birth_month_stamp)
             if age_months // 12 >= max_lifespan:
                 dead_ids.append(mid)
        
        for mid in dead_ids:
            self.remove_mortal(mid)
            
        return len(dead_ids)
