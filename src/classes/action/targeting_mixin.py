from __future__ import annotations

from typing import Optional, Iterable

from src.classes.tile import get_avatar_distance
from src.classes.observe import get_observable_avatars
from src.classes.normalize import normalize_avatar_name


class TargetingMixin:
    """
    目标与距离等通用工具：为动作类提供统一的查找与抢占能力。

    注意：不做异常吞噬，失败路径返回 None 或 False，由调用方决策。
    """
    def find_avatar_by_name(self, name: str) -> "Avatar|None":
        """
        根据名字查找角色。
        会自动规范化名字（去除括号等附加信息）以提高容错性。
        
        例如：查找 "张三（元婴）" 会自动匹配到名为 "张三" 的角色
        """
        normalized_name = normalize_avatar_name(name)
        for v in self.world.avatar_manager.avatars.values():
            if v.name == normalized_name:
                return v
        return None

    def avatars_in_same_region(self, avatar: "Avatar") -> list["Avatar"]:
        return self.world.avatar_manager.get_avatars_in_same_region(avatar)

    def avatars_on_same_tile(self, avatar: "Avatar") -> list["Avatar"]:
        result: list["Avatar"] = []
        my_tile = avatar.tile
        if my_tile is None:
            return []
        for v in self.world.avatar_manager.avatars.values():
            if v is avatar or v.tile is None:
                continue
            if v.tile == my_tile:
                result.append(v)
        return result

    def distance_between(self, a: "Avatar", b: "Avatar") -> int:
        return get_avatar_distance(a, b)

    def avatars_in_observation_range(self, avatar: "Avatar") -> list["Avatar"]:
        return self.world.avatar_manager.get_observable_avatars(avatar)

    def preempt_avatar(self, avatar: "Avatar") -> None:
        """抢占目标：清空其计划并中断当前动作。"""
        avatar.clear_plans()
        avatar.current_action = None

    def set_immediate_action(self, avatar: "Avatar", action_name: str, params: dict) -> None:
        """将动作立即加载并提交为当前动作，触发开始事件。"""
        avatar.load_decide_result_chain([(action_name, params)], avatar.thinking, "")
        avatar.commit_next_plan()


