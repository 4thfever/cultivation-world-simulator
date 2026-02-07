from __future__ import annotations
from typing import TYPE_CHECKING, Union
from src.classes.death_reason import DeathReason

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.classes.core.avatar import Avatar

def handle_death(world: World, avatar: Avatar, reason: Union[str, DeathReason]) -> None:
    """
    处理角色死亡的统一入口。
    负责将角色标记为死亡，清理行动队列，但保留角色数据。
    
    Args:
        world: 世界对象
        avatar: 死亡的角色
        reason: 死亡原因（DeathReason对象或字符串）
    """
    reason_str = str(reason)
    
    # 标记为死亡（软删除）
    avatar.set_dead(reason_str, world.month_stamp)
    
    # 从管理器中归档（硬移动），并记录变更
    world.avatar_manager.handle_death(avatar.id)
    
    # 可以在这里触发其他逻辑，比如检查是否有继承人等
