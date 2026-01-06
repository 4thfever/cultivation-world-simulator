from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING, Iterable
import itertools

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from src.classes.observe import get_observable_avatars

@dataclass
class AvatarManager:
    # 仅存储存活的角色，用于主循环遍历
    avatars: Dict[str, "Avatar"] = field(default_factory=dict)
    # 存储已死亡的角色（归档）
    dead_avatars: Dict[str, "Avatar"] = field(default_factory=dict)

    def get_avatar(self, avatar_id: str) -> "Avatar | None":
        """
        根据 ID 获取角色对象，优先查找活人，再查找死者
        """
        aid = str(avatar_id)
        return self.avatars.get(aid) or self.dead_avatars.get(aid)

    def handle_death(self, avatar_id: str) -> None:
        """
        处理角色死亡：将角色从活跃列表移动到墓地
        """
        aid = str(avatar_id)
        if aid in self.avatars:
            avatar = self.avatars.pop(aid)
            self.dead_avatars[aid] = avatar
            # 断开地图连接，确保不出现在地图网格上
            if hasattr(avatar, "tile"):
                avatar.tile = None

    def get_avatars_in_same_region(self, avatar: "Avatar") -> List["Avatar"]:
        """
        返回与给定 avatar 处于同一区域的其他【存活】角色列表（不含自己）。
        """
        if avatar is None or getattr(avatar, "tile", None) is None or avatar.tile.region is None:
            return []
        region = avatar.tile.region
        same_region: list["Avatar"] = []
        # 只遍历活人
        for other in self.avatars.values():
            if other is avatar or getattr(other, "tile", None) is None:
                continue
            if other.tile.region == region:
                same_region.append(other)
        return same_region

    def get_living_avatars(self) -> List["Avatar"]:
        """
        返回所有存活的角色列表。
        由于 avatars 现在只存活人，直接返回 values 即可。
        """
        return list(self.avatars.values())

    def get_observable_avatars(self, avatar: "Avatar") -> List["Avatar"]:
        """
        返回处于 avatar 交互范围内的其他【存活】角色列表（不含自己）。
        """
        return get_observable_avatars(avatar, self.avatars.values())
    
    def _iter_all_avatars(self) -> Iterable["Avatar"]:
        """辅助方法：遍历所有角色（活人+死者）"""
        return itertools.chain(self.avatars.values(), self.dead_avatars.values())

    def remove_avatar(self, avatar_id: str) -> None:
        """
        从管理器中彻底删除一个 avatar（无论是死是活），并清理所有与其相关的双向关系。
        此操作不可逆。
        """
        aid = str(avatar_id)
        avatar = self.get_avatar(aid)
        
        if avatar is None:
            return
            
        # 1. 清理与其直接记录的关系
        related = list(getattr(avatar, "relations", {}).keys())
        for other in related:
            avatar.clear_relation(other)
            
        # 2. 扫一遍所有角色（含死者），确保清除反向引用
        for other in self._iter_all_avatars():
            if other is avatar:
                continue
            if getattr(other, "relations", None) is not None and avatar in other.relations:
                other.clear_relation(avatar)
        
        # 3. 移除自身
        self.avatars.pop(aid, None)
        self.dead_avatars.pop(aid, None)

    def remove_avatars(self, avatar_ids: List[str]) -> None:
        """
        批量删除 avatars，并清理所有关系。
        """
        for aid in list(avatar_ids):
            self.remove_avatar(aid)
