from __future__ import annotations

from typing import TYPE_CHECKING
from src.classes.mutual_action.mutual_action import MutualAction
from src.classes.event import Event
from src.classes.action.registry import register_action
from src.classes.region import resolve_region, CultivateRegion
from src.classes.action_runtime import ActionResult, ActionStatus

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World

@register_action(actual=True)
class Occupy(MutualAction):
    """
    占据动作（互动版）：
    占据指定的洞府。如果是无主洞府直接占据；如果是有主洞府，则发起抢夺。
    """
    ACTION_NAME = "Occupy"
    COMMENT = "占据或抢夺洞府"
    
    # 参数：洞府名称
    PARAMS = {"region_name": "str"}
    
    # 对方的反馈选项（仅在抢夺时有效）
    FEEDBACK_ACTIONS = ["Yield", "Reject"]
    
    # 反馈对应的中文描述
    FEEDBACK_LABELS = {
        "Yield": "让步",
        "Reject": "拒绝",
    }
    
    # 是大事
    IS_MAJOR = True

    def _get_region_and_host(self, region_name: str) -> tuple[CultivateRegion | None, Avatar | None, str]:
        """
        解析区域并获取主人
        """
        try:
            region = resolve_region(self.world, region_name)
        except Exception as e:
            return None, None, f"无法找到区域：{region_name}"
            
        if not isinstance(region, CultivateRegion):
            return None, None, f"{region.name} 不是修炼区域，无法占据"
            
        return region, region.host_avatar, ""

    def can_start(self, region_name: str) -> tuple[bool, str]:
        region, host, err = self._get_region_and_host(region_name)
        if err:
            return False, err
            
        if region.host_avatar == self.avatar:
            return False, "已经是该洞府的主人了"
            
        return super().can_start(target_avatar=host)

    def start(self, region_name: str) -> Event:
        region, host, _ = self._get_region_and_host(region_name)
        return super().start(target_avatar=host)

    def step(self, region_name: str) -> ActionResult:
        region, host, _ = self._get_region_and_host(region_name)
        return super().step(target_avatar=host)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """
        处理反馈结果
        """
        region = self.avatar.tile.region
        if feedback_name == "Yield":
            # 对方让步：转移所有权
            region.host_avatar = self.avatar
            
            # 记录事件
            self.avatar.add_event(self.create_event(f"成功从 {target_avatar.name} 手中夺取了 {region.name}", related_avatars=[target_avatar.id]))
            target_avatar.add_event(Event(self.world.month_stamp, f"面对 {self.avatar.name} 的逼迫，不得不让出了 {region.name}", related_avatars=[self.avatar.id], is_major=True))
            
        elif feedback_name == "Reject":
            # 对方拒绝：所有权不变
            self.avatar.add_event(self.create_event(f"试图抢夺 {region.name}，但被 {target_avatar.name} 拒绝", related_avatars=[target_avatar.id]))
            target_avatar.add_event(Event(self.world.month_stamp, f"拒绝了 {self.avatar.name} 对 {region.name} 的抢夺要求", related_avatars=[self.avatar.id], is_major=True))
