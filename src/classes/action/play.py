from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event


class Play(TimedAction):
    """
    游戏娱乐动作，持续半年时间
    """

    COMMENT = "游戏娱乐，放松身心"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {}

    duration_months = 6

    def _execute(self) -> None:
        """
        进行游戏娱乐活动
        """
        # 游戏娱乐的具体逻辑可以在这里实现
        # 比如增加心情值、减少压力等
        pass

    def can_start(self) -> tuple[bool, str]:
        return True, ""

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始玩耍")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


