from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.classes.mutual_action.mutual_action import MutualAction
from src.classes.battle import decide_battle
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.classes.action.cooldown import cooldown_action

from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class Spar(MutualAction):
    """
    切磋动作：双方切磋，不造成伤害，增加武器熟练度。
    """
    ACTION_NAME = "切磋"
    DESC = "与目标切磋武艺，点到为止（大幅增加武器熟练度，不造成伤害）"
    DOABLES_REQUIREMENTS = "交互范围内可互动；不能连续执行"
    FEEDBACK_ACTIONS = ["Accept", "Reject"]
    
    # 切磋冷却：12个月
    ACTION_CD_MONTHS: int = 12

    # 专门的提示词，强调友好比试
    STORY_PROMPT = (
        "这是两人之间的友好切磋，点到为止，没有真正的伤害。"
        "重点描写双方招式的精妙和互相的印证启发。"
        "不要出现血腥或重伤描述。"
    )

    def _settle_feedback(self, target_avatar: Avatar, feedback_name: str) -> None:
        if feedback_name != "Accept":
            return

        # 判定胜负（复用战斗逻辑，但忽略返回的伤害值）
        winner, loser, _, _ = decide_battle(self.avatar, target_avatar)

        # 计算熟练度增益
        # 参考 NurtureWeapon: random.uniform(5.0, 10.0)
        base_gain = random.uniform(5.0, 10.0)
        
        # 赢家 3 倍，输家 1 倍
        winner_gain = base_gain * 3
        loser_gain = base_gain
        
        winner.increase_weapon_proficiency(winner_gain)
        loser.increase_weapon_proficiency(loser_gain)

        # 记录结果供 finish 使用
        self._last_result = (winner, loser, winner_gain, loser_gain)
        
        result_text = (
            f"{winner.name} 在切磋中略胜一筹，战胜了 {loser.name}。"
            f"（{winner.name} 熟练度+{winner_gain:.1f}，{loser.name} 熟练度+{loser_gain:.1f}）"
        )
        
        # 添加结果事件
        event = Event(
            self.world.month_stamp, 
            result_text, 
            related_avatars=[self.avatar.id, target_avatar.id]
        )
        
        # 使用 EventHelper.push_pair 确保只推送一次到 Global EventManager（通过 to_sidebar_once=True）
        # 此时 Self(Initiator) 获得 to_sidebar=True, Target 获得 to_sidebar=False
        EventHelper.push_pair(event, self.avatar, target_avatar, to_sidebar_once=True)

    async def finish(self, target_avatar: Avatar | str) -> list[Event]:
        # 获取目标
        target = self._get_target_avatar(target_avatar)
        if target is None or not hasattr(self, "_last_result"):
            return []

        winner, loser, w_gain, l_gain = self._last_result
        
        # 构造故事输入
        start_text = f"{self.avatar.name} 向 {target.name} 发起切磋"
        result_text = f"{winner.name} 战胜了 {loser.name}"

        # 生成故事
        story = await StoryTeller.tell_story(
            start_text, 
            result_text, 
            self.avatar, 
            target, 
            prompt=self.STORY_PROMPT, 
            allow_relation_changes=True
        )
        
        story_event = Event(
            self.world.month_stamp, 
            story, 
            related_avatars=[self.avatar.id, target.id], 
            is_story=True
        )
        
        # 返回给 Self (由 ActionMixin 处理)
        return [story_event]
