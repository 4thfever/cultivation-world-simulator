from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from src.classes.observe import get_observable_avatars

@dataclass
class AvatarManager:
    avatars: Dict[str, "Avatar"] = field(default_factory=dict)

    def get_avatars_in_same_region(self, avatar: "Avatar") -> List["Avatar"]:
        """
        返回与给定 avatar 处于同一区域的其他角色列表（不含自己）。
        """
        if avatar is None or getattr(avatar, "tile", None) is None or avatar.tile.region is None:
            return []
        region = avatar.tile.region
        same_region: list["Avatar"] = []
        for other in self.avatars.values():
            if other is avatar or getattr(other, "tile", None) is None:
                continue
            if other.tile.region == region:
                same_region.append(other)
        return same_region

    def get_observable_avatars(self, avatar: "Avatar") -> List["Avatar"]:
        """
        返回处于 avatar 交互范围内的其他角色列表（不含自己）。
        基于曼哈顿距离与境界映射的感知半径过滤。
        """
        return get_observable_avatars(avatar, self.avatars.values())

    def remove_avatar(self, avatar_id: str) -> None:
        """
        从管理器中删除一个 avatar，并清理所有与其相关的双向关系。
        """
        avatar = self.avatars.get(avatar_id)
        if avatar is None:
            return
        # 先清理与其直接记录的关系（会保持对称）
        related = list(getattr(avatar, "relations", {}).keys())
        for other in related:
            avatar.clear_relation(other)
        # 再次扫一遍所有 avatar，确保不存在残留引用
        for other in list(self.avatars.values()):
            if other is avatar:
                continue
            if getattr(other, "relations", None) is not None and avatar in other.relations:
                other.clear_relation(avatar)
        # 最后移除自身
        self.avatars.pop(avatar_id, None)

    def remove_avatars(self, avatar_ids: List[str]) -> None:
        """
        批量删除 avatars，并清理所有关系。
        """
        for aid in list(avatar_ids):
            self.remove_avatar(aid)


