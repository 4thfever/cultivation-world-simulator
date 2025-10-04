from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.action_runtime import ActionResult, ActionStatus
from src.utils.config import CONFIG
from src.classes.event import Event


class Talk(InstantAction):
    """
    攀谈：尝试与同区域内的某个NPC进行交谈。
    - can_start：同区域内存在其他NPC
    - 发起后：随机寻找“同一tile”的NPC，若不存在则本次无法攀谈
    - 若找到，则进入 MutualAction: Conversation（允许建立关系）
    """

    COMMENT = "与同区域内的NPC发起攀谈，若同一tile有人则进入交谈"
    DOABLES_REQUIREMENTS = "同区域内存在其他NPC"
    PARAMS = {}

    def _get_same_region_others(self) -> list["Avatar"]:
        return self.world.avatar_manager.get_avatars_in_same_region(self.avatar)

    def _get_same_tile_others(self) -> list["Avatar"]:
        same_tile: list["Avatar"] = []
        my_tile = self.avatar.tile
        if my_tile is None:
            return []
        for v in self.world.avatar_manager.avatars.values():
            if v is self.avatar or v.tile is None:
                continue
            if v.tile == my_tile:
                same_tile.append(v)
        return same_tile

    def _execute(self) -> None:
        # Talk 本身不做长期效果，主要在 step 中驱动 Conversation
        return

    def can_start(self) -> bool:
        # 是否同区域存在其他NPC（用于展示在动作空间）
        return len(self._get_same_region_others()) > 0

    def start(self) -> Event:
        self.same_region_others = self._get_same_region_others()
        # 记录开始事件
        return Event(self.world.month_stamp, f"{self.avatar.name} 尝试与同区域的他人攀谈")

    def step(self) -> ActionResult:
        import random

        target = random.choice(self.same_region_others)

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


