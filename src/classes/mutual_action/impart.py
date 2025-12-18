from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.relation import Relation
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class Impart(MutualAction):
    """传道：师傅对徒弟传授修炼经验。

    - 仅限发起方是目标的师傅（检查师徒关系）
    - 师傅等级必须大于徒弟等级20级以上
    - 目标在交互范围内
    - 目标可以选择 接受 或 拒绝
    - 若接受：徒弟获得大量修为（相当于在灵气密度5的地方修炼的4倍，即2000经验）
    """

    ACTION_NAME = "传道"
    DESC = "师傅向徒弟传授修炼经验，徒弟可获得大量修为"
    DOABLES_REQUIREMENTS = "发起者是目标的师傅；师傅等级 > 徒弟等级 + 20；目标在交互范围内；不能连续执行"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Accept", "Reject"]
    # 传道冷却：6个月
    ACTION_CD_MONTHS: int = 6

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查传道特有的启动条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, "目标不在交互范围内"

        # 检查是否是师徒关系：师傅对徒弟的关系应该是 MASTER
        relation = self.avatar.get_relation(target)
        if relation != Relation.MASTER:
            return False, "目标不是自己的徒弟"
        
        # 检查等级差
        level_diff = self.avatar.cultivation_progress.level - target.cultivation_progress.level
        if level_diff < 20:
            return False, f"等级差不足20级（当前差距：{level_diff}级）"
        
        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        event = Event(
            self.world.month_stamp,
            f"{self.avatar.name} 向徒弟 {target_name} 传道授业",
            related_avatars=rel_ids
        )
        # 仅写入历史
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        # 初始化内部标记
        self._impart_success = False
        self._impart_exp_gain = 0
        return event

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Accept":
            # 接受则当场结算修为收益（徒弟获得）
            self._apply_impart_gain(target_avatar)
            self._impart_success = True
        else:
            # 拒绝
            self._impart_success = False

    def _apply_impart_gain(self, target: "Avatar") -> None:
        # 传道经验：相当于在灵气密度5的地方修炼的4倍
        # base_exp = 100, density = 5, 倍数 = 4
        # 总经验 = 100 * 5 * 4 = 2000
        exp_gain = 100 * 5 * 4
        target.cultivation_progress.add_exp(exp_gain)
        self._impart_exp_gain = exp_gain

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        target = self._get_target_avatar(target_avatar)
        events: list[Event] = []
        success = self._impart_success
        if target is None:
            return events

        if success:
            gain = int(self._impart_exp_gain)
            result_text = f"{target.name} 获得修为经验 +{gain} 点"
            result_event = Event(
                self.world.month_stamp,
                result_text,
                related_avatars=[self.avatar.id, target.id]
            )
            events.append(result_event)

        return events

