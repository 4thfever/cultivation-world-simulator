from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event


class Play(TimedAction):
    """
    消遣动作，持续半年时间
    """

    ACTION_NAME = "消遣"
    EMOJI = "🪁"
    DESC = "消遣，放松身心"
    DOABLES_REQUIREMENTS = "无限制"
    PARAMS = {}

    duration_months = 6

    def _execute(self) -> None:
        """
        进行消遣活动
        """
        # 消遣的具体逻辑可以在这里实现
        # 比如增加心情值、减少压力等
        pass

    def can_start(self) -> tuple[bool, str]:
        return True, ""

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始消遣", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


