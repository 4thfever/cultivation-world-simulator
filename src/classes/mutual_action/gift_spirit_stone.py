from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.event import Event
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class GiftSpiritStone(MutualAction):
    """赠送灵石：向目标赠送灵石。

    - 发起方灵石必须足够（至少100灵石）
    - 目标在交互范围内
    - 目标可以选择 接受 或 拒绝
    - 若接受：发起方扣除100灵石，目标获得100灵石
    """

    ACTION_NAME = "赠送灵石"
    EMOJI = "🎁"
    DESC = "向对方赠送灵石，一次赠送100灵石"
    DOABLES_REQUIREMENTS = "发起者至少有100灵石；目标在交互范围内"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Accept", "Reject"]

    # 默认赠送数量
    GIFT_AMOUNT = 100

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查赠送灵石的启动条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, "目标不在交互范围内"

        # 检查发起者的灵石是否足够
        if self.avatar.magic_stone < self.GIFT_AMOUNT:
            return False, f"灵石不足（当前：{self.avatar.magic_stone}，需要：{self.GIFT_AMOUNT}）"
        
        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        event = Event(
            self.world.month_stamp,
            f"{self.avatar.name} 向 {target_name} 赠送 {self.GIFT_AMOUNT} 灵石",
            related_avatars=rel_ids
        )
        # 仅写入历史
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        # 初始化内部标记
        self._gift_success = False
        return event

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Accept":
            # 接受则当场结算灵石转移
            self._apply_gift(target_avatar)
            self._gift_success = True
        else:
            # 拒绝
            self._gift_success = False

    def _apply_gift(self, target: "Avatar") -> None:
        """执行灵石转移"""
        # 从发起者扣除灵石
        self.avatar.magic_stone -= self.GIFT_AMOUNT
        # 目标获得灵石
        target.magic_stone += self.GIFT_AMOUNT

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        target = self._get_target_avatar(target_avatar)
        events: list[Event] = []
        success = self._gift_success
        if target is None:
            return events

        if success:
            result_text = f"{self.avatar.name} 赠送了 {self.GIFT_AMOUNT} 灵石给 {target.name}（{self.avatar.
            name} 灵石：{self.avatar.magic_stone + self.GIFT_AMOUNT} → {self.avatar.magic_stone}，{target.
            name} 灵石：{target.magic_stone - self.GIFT_AMOUNT} → {target.magic_stone}）"
            result_event = Event(
                self.world.month_stamp,
                result_text,
                related_avatars=[self.avatar.id, target.id]
            )
            events.append(result_event)
        return events

