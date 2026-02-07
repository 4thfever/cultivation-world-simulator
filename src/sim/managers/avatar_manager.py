from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING, Iterable
import itertools

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from src.classes.observe import get_observable_avatars

@dataclass
class AvatarManager:
    # 仅存储存活的角色，用于主循环遍历
    avatars: Dict[str, "Avatar"] = field(default_factory=dict)
    # 存储已死亡的角色（归档）
    dead_avatars: Dict[str, "Avatar"] = field(default_factory=dict)
    
    # --- 变更缓冲区 (不参与序列化) ---
    _newly_dead_buffer: List[str] = field(default_factory=list, init=False)
    _newly_born_buffer: List[str] = field(default_factory=list, init=False)

    def register_avatar(self, avatar: "Avatar", is_newly_born: bool = False) -> None:
        """
        注册一个角色到管理器中。
        Args:
            avatar: 角色对象
            is_newly_born: 是否为新出生的角色（若是，则加入变更缓冲供前端同步）
        """
        self.avatars[str(avatar.id)] = avatar
        if is_newly_born:
            self._newly_born_buffer.append(str(avatar.id))

    def pop_newly_dead(self) -> List[str]:
        """获取并清空本帧刚死亡的角色ID列表"""
        res = list(self._newly_dead_buffer)
        self._newly_dead_buffer.clear()
        return res

    def pop_newly_born(self) -> List[str]:
        """获取并清空本帧刚出生的角色ID列表"""
        res = list(self._newly_born_buffer)
        self._newly_born_buffer.clear()
        return res

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
            
            # 记录变更
            self._newly_dead_buffer.append(aid)

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

    def cleanup_long_dead_avatars(self, current_time: "MonthStamp", threshold_years: int = 20) -> int:
        """
        清理长期已故的角色。
        
        Args:
            current_time: 当前时间戳
            threshold_years: 死亡超过多少年则清理 (默认20年)
            
        Returns:
            清理的角色数量
        """
        if not self.dead_avatars:
            return 0
            
        to_remove = []
        for aid, avatar in self.dead_avatars.items():
            if avatar.death_info:
                death_time = avatar.death_info.get("time") # int 类型的时间戳
                if death_time is not None:
                    # 计算时间差 (MonthStamp 本质是 int, 表示总月数)
                    elapsed_months = int(current_time) - death_time
                    elapsed_years = elapsed_months // 12
                    
                    if elapsed_years >= threshold_years:
                        to_remove.append(aid)
        
        # 批量删除
        if to_remove:
            self.remove_avatars(to_remove)
            
        return len(to_remove)

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

        # 2. 清理占据的洞府
        if hasattr(avatar, "owned_regions") and avatar.owned_regions:
            for region in list(avatar.owned_regions):
                # 仅解除关系，不触发其他逻辑
                if region.host_avatar == avatar:
                    region.host_avatar = None
            avatar.owned_regions.clear()
            
        # 3. 扫一遍所有角色（含死者），确保清除反向引用
        for other in self._iter_all_avatars():
            if other is avatar:
                continue
            if getattr(other, "relations", None) is not None and avatar in other.relations:
                other.clear_relation(avatar)
        
        # 4. 清理宗门关系
        if getattr(avatar, "sect", None) is not None:
            # 必须调用 sect.remove_member 以从宗门成员字典中移除
            # 注意：不应调用 avatar.leave_sect()，因为它可能修改 avatar.sect 为 None，
            # 而我们这里主要关注清理外部（Sect对象）对 avatar 的引用。
            avatar.sect.remove_member(avatar)

        # 5. 移除自身
        self.avatars.pop(aid, None)
        self.dead_avatars.pop(aid, None)

    def remove_avatars(self, avatar_ids: List[str]) -> None:
        """
        批量删除 avatars，并清理所有关系。
        """
        for aid in list(avatar_ids):
            self.remove_avatar(aid)
