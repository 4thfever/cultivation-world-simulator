from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.world import World
    from src.classes.avatar import Avatar

def handle_death(world: World, avatar: Avatar) -> None:
    """
    处理角色死亡的统一入口。
    负责将角色从世界管理器中移除，并处理相关的清理工作（如关系解除已在 remove_avatar 中实现）。
    注意：本函数不负责生成死亡事件文本，调用者应在调用前生成相应的 Event。
    """
    # 从管理器中移除角色（remove_avatar 内部会自动清理双向关系）
    world.avatar_manager.remove_avatar(avatar.id)

