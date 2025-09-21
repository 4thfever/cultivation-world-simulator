from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


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


