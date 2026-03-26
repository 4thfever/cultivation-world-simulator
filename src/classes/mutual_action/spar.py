from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.mutual_action.mutual_action import InvitationAction
from src.systems.battle import decide_battle
from src.classes.event import Event
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.action.cooldown import cooldown_action

from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@cooldown_action
class Spar(InvitationAction):
    """
    切磋动作：双方切磋，不造成伤害，增加武器熟练度。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "spar_action_name"
    DESC_ID = "spar_description"
    REQUIREMENTS_ID = "spar_requirements"
    STORY_PROMPT_ID = "spar_story_prompt"
    
    # 不需要翻译的常量
    EMOJI = "🤺"
    PARAMS = {"target_avatar": "AvatarName"}
    RESPONSE_ACTIONS = ["Accept", "Reject"]
    
    # 切磋冷却：12个月
    ACTION_CD_MONTHS: int = 12

    def _settle_response(self, target_avatar: Avatar, response_name: str) -> None:
        if response_name != "Accept":
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
        
        result_text = t("{winner} gained slight advantage in sparring, defeated {loser}. ({winner} proficiency +{w_gain}, {loser} proficiency +{l_gain})",
                       winner=winner.name, loser=loser.name, 
                       w_gain=f"{winner_gain:.1f}", l_gain=f"{loser_gain:.1f}")
        
        # 添加结果事件
        event = Event(
            self.world.month_stamp, 
            result_text, 
            related_avatars=[self.avatar.id, target_avatar.id]
        )
        
        # 使用 EventHelper.push_pair 确保只推送一次到 Global EventManager（通过 to_sidebar_once=True）
        # 此时 Self(Initiator) 获得 to_sidebar=True, Target 获得 to_sidebar=False
        EventHelper.push_pair(event, self.avatar, target_avatar, to_sidebar_once=True)
        self._last_result_text = result_text

    async def finish(self, target_avatar: Avatar | str) -> list[Event]:
        # 获取目标
        target = self._get_target_avatar(target_avatar)
        if target is None or not hasattr(self, "_last_result"):
            return []

        winner, loser, w_gain, l_gain = self._last_result
        result_text = getattr(self, "_last_result_text", t("{winner} defeated {loser}", winner=winner.name, loser=loser.name))
        a_to_b, b_to_a = await RelationDeltaService.resolve_event_text_delta(
            action_key="spar",
            avatar_a=self.avatar,
            avatar_b=target,
            event_text=result_text,
        )
        RelationDeltaService.apply_bidirectional_delta(self.avatar, target, a_to_b, b_to_a)
        
        # 构造故事输入
        start_text = t("{initiator} challenges {target} to spar",
                      initiator=self.avatar.name, target=target.name)
        result_text = t("{winner} defeated {loser}", winner=winner.name, loser=loser.name)

        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.COMBAT,
            month_stamp=self.world.month_stamp,
            start_text=start_text,
            result_text=result_text,
            actors=[self.avatar, target],
            related_avatar_ids=[self.avatar.id, target.id],
            prompt=self.get_story_prompt(),
            allow_relation_changes=True,
        )

        return [story_event] if story_event is not None else []
