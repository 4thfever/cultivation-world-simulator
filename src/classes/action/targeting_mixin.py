from __future__ import annotations

from typing import Optional, Iterable, TYPE_CHECKING

from src.classes.environment.tile import get_avatar_distance
from src.classes.observe import get_observable_avatars
from src.utils.normalize import normalize_avatar_name
from src.utils.resolution import resolve_query
# 注意：避免在此处直接引入 Avatar 导致循环引用，使用 TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class TargetingMixin:
    """
    目标与距离等通用工具：为动作类提供统一的查找与抢占能力。

    注意：不做异常吞噬，失败路径返回 None 或 False，由调用方决策。
    """
    def find_avatar_by_name(self, name: str) -> "Avatar|None":
        """
        根据名字查找角色。
        会自动规范化名字（去除括号等附加信息）以提高容错性。
        """
            
        # 动态导入 Avatar 类以进行类型检查，或者直接依赖 resolve_query 的内部逻辑
        # 这里 resolve_query 需要 world 上下文
        from src.classes.core.avatar import Avatar
        res = resolve_query(name, self.world, expected_types=[Avatar])
        return res.obj

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

    def validate_target_avatar(self, name: str | None) -> tuple["Avatar | None", bool, str]:
        """
        验证目标角色是否有效（存在且存活）。

        Args:
            name: 目标角色名。

        Returns:
            (target, can_proceed, reason)
            - target: 找到的角色对象，无效时为 None。
            - can_proceed: 是否可以继续。
            - reason: 失败原因（成功时为空字符串）。
        """
        if not name:
            return None, False, "缺少目标参数"
        target = self.find_avatar_by_name(name)
        if target is None:
            return None, False, "目标不存在"
        if target.is_dead:
            return None, False, "目标已死亡"
        return target, True, ""
