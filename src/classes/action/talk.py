from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.action_runtime import ActionResult, ActionStatus
from src.utils.config import CONFIG
from src.classes.event import Event


class Talk(InstantAction):
    """
    攀谈：尝试与感知范围内的某个NPC进行交谈。
    - can_start：感知范围内存在其他NPC
    - 发起后：从感知范围内随机选择一个目标，进入 MutualAction: Conversation（允许建立关系）
    """

    COMMENT = "与感知范围内的NPC发起攀谈"
    DOABLES_REQUIREMENTS = "感知范围内存在其他NPC"
    PARAMS = {}

    def _get_observed_others(self) -> list["Avatar"]:
        return self.world.avatar_manager.get_observable_avatars(self.avatar)

    # 不再限定必须同一 tile，由感知范围统一约束

    def _execute(self) -> None:
        # Talk 本身不做长期效果，主要在 step 中驱动 Conversation
        return

    def can_start(self) -> bool:
        # 感知范围内是否存在其他NPC（用于展示在动作空间）
        return len(self._get_observed_others()) > 0

    def start(self) -> Event:
        self.observed_others = self._get_observed_others()
        # 记录开始事件
        return Event(self.world.month_stamp, f"{self.avatar.name} 尝试与感知范围内的他人攀谈")

    def step(self) -> ActionResult:
        import random

        target = random.choice(self.observed_others)

        # 进入交谈：由概率决定本次是否允许建立关系
        from src.classes.mutual_action import Conversation
        # 由配置决定本次是否有“有机会进入关系”标记
        prob = CONFIG.social.talk_into_relation_probability
        can_into_relation = random.random() < prob

        conv = Conversation(self.avatar, self.world)
        # 启动事件写入历史，不入侧边栏
        conv.start(target_avatar=target)
        conv.step(target_avatar=target, can_into_relation=can_into_relation)
        return ActionResult(status=ActionStatus.COMPLETED, events=[])

    def finish(self) -> list[Event]:
        return []


