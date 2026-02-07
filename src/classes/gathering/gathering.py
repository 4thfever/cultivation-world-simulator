from abc import ABC, abstractmethod
from typing import List, Type, TYPE_CHECKING

from src.classes.event import Event

if TYPE_CHECKING:
    from src.classes.core.world import World

class Gathering(ABC):
    """
    多人聚集事件/场景的抽象基类。
    用于处理如“拍卖会”、“宗门大比”、“秘境开启”等多角色参与的复杂事件。
    """
    
    @abstractmethod
    def is_start(self, world: "World") -> bool:
        """
        检测该 Gathering 是否应该开始。
        通常基于时间、地点或特定触发条件。
        """
        pass

    @abstractmethod
    def get_related_avatars(self, world: "World") -> List[int]:
        """
        获取参与该 Gathering 的角色 ID 列表。
        """
        pass

    @abstractmethod
    def get_info(self, world: "World") -> str:
        """
        获取 Gathering 的描述信息。
        """
        pass

    @abstractmethod
    async def execute(self, world: "World") -> List[Event]:
        """
        执行 Gathering 的具体逻辑。
        
        备注：
        因为 Gathering 被设计为瞬时结算（在一个 step 内完成），
        所以不需要 finish 函数。所有的交互和结果都在 execute 中一次性处理完毕。
        """
        pass

# Global registry for Gathering classes
GATHERING_REGISTRY: List[Type[Gathering]] = []

def register_gathering(cls: Type[Gathering]):
    """
    装饰器：注册 Gathering 类
    """
    GATHERING_REGISTRY.append(cls)
    return cls

class GatheringManager:
    def __init__(self):
        # 实例化所有注册的 Gathering
        self.gatherings: List[Gathering] = [cls() for cls in GATHERING_REGISTRY]

    async def check_and_run_all(self, world: "World") -> List[Event]:
        """
        检查所有 Gathering，若满足条件则执行
        """
        events = []
        for gathering in self.gatherings:
            if gathering.is_start(world):
                # 执行 Gathering 逻辑
                gathering_events = await gathering.execute(world)
                if gathering_events:
                    events.extend(gathering_events)
        return events
