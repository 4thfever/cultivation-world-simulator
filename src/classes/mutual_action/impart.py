from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.i18n import t
from .mutual_action import MutualAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.relation.relation import Relation
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@cooldown_action
class Impart(MutualAction):
    """传道：向指定关系的目标传授修炼经验。

    - 仅限发起方的徒弟、徒孙、同门、子女、孙辈或朋友
    - 发起方等级必须大于目标等级20级以上
    - 目标在交互范围内
    - 目标可以选择 接受 或 拒绝
    - 若接受：目标获得大量修为（相当于在灵气密度5的地方修炼的4倍，即2000经验）
    """

    # 多语言 ID
    ACTION_NAME_ID = "impart_action_name"
    DESC_ID = "impart_description"
    REQUIREMENTS_ID = "impart_requirements"

    # 不需要翻译的常量
    EMOJI = "📖"
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
            return False, t("Target not within interaction range")

        # 检查是否满足传道关系
        rel = self.avatar.get_relation(target) or getattr(self.avatar, "computed_relations", {}).get(target)
        
        allowed_relations = {
            Relation.IS_DISCIPLE_OF,             # 徒弟
            Relation.IS_MARTIAL_GRANDCHILD_OF,   # 徒孙
            Relation.IS_MARTIAL_SIBLING_OF,      # 同门
            Relation.IS_CHILD_OF,                # 儿子/女儿
            Relation.IS_GRAND_CHILD_OF,          # 孙子/孙女
            Relation.IS_FRIEND_OF,               # 朋友
        }

        if rel not in allowed_relations:
            return False, t("Target is not your disciple, martial grandchild, martial sibling, child, grandchild, or friend")

        # 检查等级差
        level_diff = self.avatar.cultivation_progress.level - target.cultivation_progress.level
        if level_diff < 20:
            return False, t(
                "Level difference insufficient, need 20 levels (current gap: {diff} levels)",
                diff=level_diff,
            )

        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)

        content = t(
            "{giver} imparts cultivation knowledge to {receiver}",
            giver=self.avatar.name,
            receiver=target_name,
        )
        event = Event(
            self.world.month_stamp,
            content,
            related_avatars=rel_ids,
        )

        # 初始化内部标记
        self._impart_success = False
        self._impart_exp_gain = 0
        return event

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Accept":
            # 接受则当场结算修为收益（接收者获得）
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
            result_text = t(
                "{avatar} gained cultivation experience +{exp} points",
                avatar=target.name,
                exp=gain,
            )
            result_event = Event(
                self.world.month_stamp,
                result_text,
                related_avatars=[self.avatar.id, target.id],
            )
            events.append(result_event)

        return events