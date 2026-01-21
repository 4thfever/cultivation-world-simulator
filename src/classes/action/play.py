from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event


class Play(TimedAction):
    """
    消遣动作，持续半年时间
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "play_action_name"
    DESC_ID = "play_description"
    REQUIREMENTS_ID = "play_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🪁"
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
        from src.i18n import t
        content = t("{avatar} begins leisure activities", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


