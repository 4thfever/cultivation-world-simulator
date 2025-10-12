from __future__ import annotations

from src.classes.action import DefineAction, ActualActionMixin
from src.classes.event import Event
from src.classes.region import Region
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority


class MoveToRegion(DefineAction, ActualActionMixin):
    """
    移动到某个region
    """

    COMMENT = "移动到某个区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "region_name"}

    def _normalize_region_name(self, name: str) -> str:
        """
        将诸如 "太白金府（金行灵气：10）" 归一化为 "太白金府"。
        去除常见括号及其中附加信息，并裁剪空白。
        """
        s = name.strip()
        brackets = [("(", ")"), ("（", "）"), ("[", "]"), ("【", "】"), ("「", "」"), ("『", "』"), ("<", ">"), ("《", "》")]
        for left, right in brackets:
            # 连续移除所有成对括号内容
            while True:
                start = s.find(left)
                end = s.rfind(right)
                if start != -1 and end != -1 and end > start:
                    s = (s[:start] + s[end + 1:]).strip()
                else:
                    break
        return s

    def _resolve_region(self, region: Region | str) -> Region:
        """
        将字符串或 Region 实例解析为当前 world.map 中的 Region 实例：
        - 字符串：从 world.map.region_names 查找，不存在则抛出 ValueError
        - Region 实例：若存在 world.map.regions（按 id 索引），则按 id 映射到当前实例，否则直接返回传入实例
        """
        if isinstance(region, str):
            region_name = region
            by_name = self.world.map.region_names

            # 1) 精确匹配
            r = by_name.get(region_name)
            if r is not None:
                return r

            # 2) 归一化后再精确匹配
            normalized = self._normalize_region_name(region_name)
            if normalized and normalized != region_name:
                r2 = by_name.get(normalized)
                if r2 is not None:
                    return r2

            # 3) 唯一包含匹配（当且仅当候选唯一时）
            candidates = [name for name in by_name.keys() if name and (name in region_name or (normalized and name in normalized))]
            if len(candidates) == 1:
                return by_name[candidates[0]]

            # 失败：抛出明确错误提示
            if candidates:
                sample = ", ".join(candidates[:5])
                raise ValueError(f"区域名不唯一: {region_name}，候选: {sample}")
            raise ValueError(f"未知区域名: {region_name}")
        if isinstance(region, Region):
            by_id = getattr(self.world.map, "regions", None)
            if isinstance(by_id, dict) and region.id in by_id:
                return by_id[region.id]
            return region
        raise TypeError(f"不支持的region类型: {type(region).__name__}")

    def _execute(self, region: Region | str) -> None:
        """
        移动到某个region
        """
        region = self._resolve_region(region)
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        raw_dx = region_center_loc[0] - cur_loc[0]
        raw_dy = region_center_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, region: Region | str | None = None) -> bool:
        return True

    def start(self, region: Region | str) -> Event:
        r = self._resolve_region(region)
        region_name = r.name  # 仅使用规范化后的区域名
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        # 完成条件：到达目标区域
        r = self._resolve_region(region)
        done = self.avatar.is_in_region(r if isinstance(r, Region) else None)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    def finish(self, region: Region | str) -> list[Event]:
        return []


