"""
NPC AI的类。
这里指的不是LLM或者Machine Learning，而是NPC的决策机制
分为两类：规则AI和LLM AI
"""
from abc import ABC, abstractmethod

from src.classes.world import World
from src.classes.tile import Region
from src.classes.root import corres_essence_type

class AI(ABC):
    """
    AI的基类
    """
    def __init__(self, avatar: 'Avatar'):
        self.avatar = avatar

    @abstractmethod
    def decide(self, world: World) -> tuple[str, dict]:
        """
        决定做什么
        """
        pass

    # def create_event(self, world: World, content: str) -> Event:
    #     """
    #     创建事件
    #     """
    #     return Event(world.year, world.month, content)

class RuleAI(AI):
    """
    规则AI
    """
    def decide(self, world: World) -> tuple[str, dict]:
        """
        决定做什么
        先做一个简单的：
        1. 找到自己灵根对应的最好的区域
        2. 检测自己是否在最好的区域
        3. 如果不在，则移动到最好的区域
        4. 如果已经到达最好的区域，则进行修炼
        5. 如果需要突破境界了，则突破境界
        """
        best_region = self.get_best_region(list(world.map.regions.values()))
        if self.avatar.is_in_region(best_region):
            if self.avatar.cultivation_progress.can_break_through():
                return "Breakthrough", {}
            else:
                return "Cultivate", {}
        else:
            return "MoveToRegion", {"region": best_region}
    
    def get_best_region(self, regions: list[Region]) -> Region:
        """
        根据avatar的灵根找到最适合的区域
        """
        root = self.avatar.root
        essence_type = corres_essence_type[root]
        region_with_best_essence = max(regions, key=lambda region: region.essence.get_density(essence_type))
        return region_with_best_essence
        
class LLMAI(AI):
    """
    LLM AI
    """
    def decide(self, world: World) -> tuple[str, dict]:
        """
        决定做什么
        """
        pass