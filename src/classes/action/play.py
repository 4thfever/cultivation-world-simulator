from __future__ import annotations
import random
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.action.action import TimedAction
from src.classes.action_runtime import ActionStatus
from src.classes.event import Event
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World

class BasePlayAction(TimedAction):
    """消遣动作基类"""
    duration_months = 1
    REQUIREMENTS_ID = "play_requirements"

    def __init__(self, avatar: Avatar, world: World):
        super().__init__(avatar, world)

    def _try_trigger_benefit(self) -> str:
        """尝试触发额外收益 (突破概率)"""
        prob = CONFIG.play.base_benefit_probability if hasattr(CONFIG, 'play') else 0.05
        
        if random.random() < prob:
            rate = 0.2
            self.avatar.add_breakthrough_rate(rate)
            return t("breakthrough probability increased by {val:.1%}", val=rate)
        return ""

    def _execute(self) -> None:
        pass # 具体逻辑由子类实现或只需记录事件

    def start(self) -> Event:
        # 通用开始事件
        return Event(self.world.month_stamp, t("{avatar} starts {action}", avatar=self.avatar.name, action=self.get_action_name()), related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        # 结算时尝试触发收益
        benefit_msg = self._try_trigger_benefit()
        content = t("{avatar} finished {action}.", avatar=self.avatar.name, action=self.get_action_name())
        if benefit_msg:
            content += f" {benefit_msg}"
        
        return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]

# 具体动作实现
class Reading(BasePlayAction):
    ACTION_NAME_ID = "action_reading"
    DESC_ID = "action_reading_desc"
    EMOJI = "📖"

class TeaTasting(BasePlayAction):
    ACTION_NAME_ID = "action_tea_tasting"
    DESC_ID = "action_tea_tasting_desc"
    EMOJI = "🍵"

class Traveling(BasePlayAction):
    ACTION_NAME_ID = "action_traveling"
    DESC_ID = "action_traveling_desc"
    EMOJI = "🧳"

class ZitherPlaying(BasePlayAction):
    ACTION_NAME_ID = "action_zither_playing"
    DESC_ID = "action_zither_playing_desc"
    EMOJI = "🎵"
